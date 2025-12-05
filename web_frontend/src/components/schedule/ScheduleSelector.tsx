import type { DayName, AvailabilityData } from "../../types/signup";
import { DAY_NAMES } from "../../types/signup";
import { useScheduleSelection } from "./useScheduleSelection";

interface ScheduleSelectorProps {
  value: AvailabilityData;
  onChange: (data: AvailabilityData) => void;
  startHour?: number;
  endHour?: number;
}

const SHORT_DAY_NAMES: Record<DayName, string> = {
  Monday: "Mon",
  Tuesday: "Tue",
  Wednesday: "Wed",
  Thursday: "Thu",
  Friday: "Fri",
  Saturday: "Sat",
  Sunday: "Sun",
};

function formatHour(hour: number): string {
  if (hour === 0) return "12am";
  if (hour === 12) return "12pm";
  if (hour < 12) return `${hour}am`;
  return `${hour - 12}pm`;
}

interface TimeSlotCellProps {
  day: DayName;
  hour: number;
  isSelected: boolean;
  isPreview: boolean;
  selectionMode: "add" | "remove" | null;
  onMouseDown: () => void;
  onMouseEnter: () => void;
  onTouchStart: () => void;
}

function TimeSlotCell({
  day,
  hour,
  isSelected,
  isPreview,
  selectionMode,
  onMouseDown,
  onMouseEnter,
  onTouchStart,
}: TimeSlotCellProps) {
  let bgClass = "bg-gray-200 hover:bg-gray-300";

  if (isPreview) {
    // During drag, show preview state
    if (selectionMode === "add") {
      bgClass = "bg-blue-300";
    } else {
      bgClass = "bg-red-200";
    }
  } else if (isSelected) {
    bgClass = "bg-blue-500";
  }

  return (
    <div
      data-day={day}
      data-hour={hour}
      className={`h-6 border border-gray-300 cursor-pointer select-none touch-none transition-colors ${bgClass}`}
      onMouseDown={onMouseDown}
      onMouseEnter={onMouseEnter}
      onTouchStart={onTouchStart}
    />
  );
}

export default function ScheduleSelector({
  value,
  onChange,
  startHour = 8,
  endHour = 22,
}: ScheduleSelectorProps) {
  const hours = Array.from(
    { length: endHour - startHour },
    (_, i) => startHour + i,
  );

  const { gridRef, selectionState, isSelected, isPreview, handlers } =
    useScheduleSelection({
      value,
      onChange,
      hours,
    });

  const totalSelected = Object.values(value).reduce(
    (sum, slots) => sum + slots.length,
    0,
  );

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Click and drag to select your available times
        </p>
        <span className="text-sm font-medium text-gray-700">
          {totalSelected} slot{totalSelected !== 1 ? "s" : ""} selected
        </span>
      </div>

      <div
        ref={gridRef}
        className="grid select-none overflow-x-auto"
        style={{
          gridTemplateColumns: "50px repeat(7, minmax(40px, 1fr))",
        }}
        onMouseLeave={() => {
          // Don't end selection on mouse leave - let global handler do it
        }}
      >
        {/* Header row: empty corner + day names */}
        <div className="sticky left-0 bg-white" />
        {DAY_NAMES.map((day) => (
          <div
            key={day}
            className="text-center font-medium text-sm py-2 text-gray-700"
          >
            {SHORT_DAY_NAMES[day]}
          </div>
        ))}

        {/* Time rows */}
        {hours.map((hour) => (
          <>
            {/* Time label */}
            <div
              key={`label-${hour}`}
              className="sticky left-0 bg-white text-right pr-2 text-xs text-gray-500 flex items-center justify-end"
            >
              {formatHour(hour)}
            </div>

            {/* Day cells for this hour */}
            {DAY_NAMES.map((day) => (
              <TimeSlotCell
                key={`${day}-${hour}`}
                day={day}
                hour={hour}
                isSelected={isSelected(day, hour)}
                isPreview={isPreview(day, hour)}
                selectionMode={selectionState.selectionMode}
                onMouseDown={() => handlers.onMouseDown(day, hour)}
                onMouseEnter={() => handlers.onMouseEnter(day, hour)}
                onTouchStart={() => handlers.onTouchStart(day, hour)}
              />
            ))}
          </>
        ))}

        {/* Final time label row */}
        <div className="sticky left-0 bg-white text-right pr-2 text-xs text-gray-500 flex items-start justify-end pt-1">
          {formatHour(endHour)}
        </div>
        {DAY_NAMES.map((day) => (
          <div key={`empty-${day}`} />
        ))}
      </div>

      <div className="mt-4 flex gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-200 border border-gray-300" />
          <span className="text-gray-600">Not available</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 border border-gray-300" />
          <span className="text-gray-600">Available</span>
        </div>
      </div>
    </div>
  );
}
