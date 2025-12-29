"""
Scheduler Cog - Discord adapter for the scheduling algorithm.
"""

import discord
from discord import app_commands
from discord.ext import commands

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import (
    format_time_range, calculate_total_available_time,
    get_people_for_scheduling,
    schedule as run_schedule, SchedulingError, NoUsersError, NoFacilitatorsError
)


class SchedulerCog(commands.Cog):
    """Cog for cohort scheduling functionality."""

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="schedule", description="Run the cohort scheduling algorithm")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        meeting_length="Meeting length in minutes (default: 60)",
        min_people="Minimum people per cohort (default: 4)",
        max_people="Maximum people per cohort (default: 8)",
        iterations="Number of iterations to run (default: 1000)",
        balance="Balance cohort sizes after scheduling (default: True)",
        use_if_needed="Include 'if needed' times in scheduling (default: True)",
        facilitator_mode="Require each cohort to have one facilitator (default: False)"
    )
    async def schedule(self, interaction: discord.Interaction,
                       meeting_length: int = 60,
                       min_people: int = 4,
                       max_people: int = 8,
                       iterations: int = 1000,
                       balance: bool = True,
                       use_if_needed: bool = True,
                       facilitator_mode: bool = False):
        """Run the scheduling algorithm on all registered users."""

        await interaction.response.defer()

        # Progress message
        progress_msg = await interaction.followup.send(
            "Running scheduling algorithm...",
            ephemeral=False
        )

        async def update_progress(course_name, current, total, best_score, total_people):
            try:
                await progress_msg.edit(
                    content=f"Scheduling **{course_name}**...\n"
                            f"Iteration: {current}/{total} | "
                            f"Best: {best_score}/{total_people}"
                )
            except:
                pass

        # Run scheduling (all business logic is in core)
        try:
            result = await run_schedule(
                meeting_length=meeting_length,
                min_people=min_people,
                max_people=max_people,
                num_iterations=iterations,
                balance=balance,
                use_if_needed=use_if_needed,
                facilitator_mode=facilitator_mode,
                progress_callback=update_progress
            )
        except NoUsersError:
            await progress_msg.edit(content="No users have set their availability yet!")
            return
        except NoFacilitatorsError:
            await progress_msg.edit(
                content="Facilitator mode is enabled but no facilitators are marked!\n"
                        "Use `/toggle-facilitator` to mark people as facilitators."
            )
            return

        # Build results embed
        placement_rate = result.total_scheduled * 100 // result.total_people if result.total_people else 0

        embed = discord.Embed(
            title="Scheduling Complete!",
            color=discord.Color.green() if placement_rate >= 80 else discord.Color.yellow()
        )

        balance_info = f"\n**Balance moves:** {result.total_balance_moves}" if result.total_balance_moves > 0 else ""
        embed.add_field(
            name="Summary",
            value=f"**Courses:** {len(result.course_results)}\n"
                  f"**Total cohorts:** {result.total_cohorts}\n"
                  f"**People scheduled:** {result.total_scheduled}/{result.total_people} ({placement_rate}%){balance_info}",
            inline=False
        )

        # List cohorts by course
        cohort_num = 1
        for course_name, course_result in result.course_results.items():
            if course_result.groups:
                embed.add_field(
                    name=f"{course_name}",
                    value=f"{len(course_result.groups)} cohort(s), {course_result.score} people",
                    inline=False
                )

                for group in course_result.groups:
                    members = [p.name for p in group.people]
                    time_str = format_time_range(*group.selected_time) if group.selected_time else "No common time"

                    embed.add_field(
                        name=f"Cohort {cohort_num} ({len(group.people)} people)",
                        value=f"**Time (UTC):** {time_str}\n"
                              f"**Members:** {', '.join(members)}",
                        inline=False
                    )
                    cohort_num += 1

            # Show unassigned for this course
            if course_result.unassigned:
                unassigned_names = [p.name for p in course_result.unassigned]
                embed.add_field(
                    name=f"{course_name} - Unassigned ({len(course_result.unassigned)})",
                    value=", ".join(unassigned_names[:10]) + ("..." if len(unassigned_names) > 10 else ""),
                    inline=False
                )

        await progress_msg.edit(content=None, embed=embed)

    @app_commands.command(name="list-users", description="List all users with availability")
    async def list_users(self, interaction: discord.Interaction):
        """List all users who have set their availability."""

        # Load people from database
        people, user_data = await get_people_for_scheduling()

        if not people:
            await interaction.response.send_message(
                "No users have set their availability yet. Use `/signup` to register!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Registered Users ({len(people)})",
            color=discord.Color.blue()
        )

        for person in people[:25]:  # Show max 25
            total_time = calculate_total_available_time(person)
            hours = total_time // 60

            # Check facilitator status
            is_facilitator = user_data.get(person.id, {}).get("is_facilitator", False)
            facilitator_badge = " *" if is_facilitator else ""

            courses_str = ", ".join(person.courses) if person.courses else "N/A"
            embed.add_field(
                name=f"{person.name}{facilitator_badge}",
                value=f"Available: {hours}h/week\n"
                      f"Courses: {courses_str}",
                inline=True
            )

        if len(people) > 25:
            embed.set_footer(text=f"... and {len(people) - 25} more | * = Facilitator")
        else:
            embed.set_footer(text="* = Facilitator")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))
