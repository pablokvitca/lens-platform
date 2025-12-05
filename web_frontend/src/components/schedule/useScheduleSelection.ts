import { useState, useCallback, useEffect, useRef } from "react";
import type { DayName, AvailabilityData } from "../../types/signup";
import { DAY_NAMES, formatTimeSlot } from "../../types/signup";

interface CellPosition {
  day: DayName;
  hour: number;
}

interface SelectionState {
  isSelecting: boolean;
  startCell: CellPosition | null;
  currentCell: CellPosition | null;
  selectionMode: "add" | "remove" | null;
}

interface UseScheduleSelectionOptions {
  value: AvailabilityData;
  onChange: (data: AvailabilityData) => void;
  hours: number[];
}

function getSelectedCells(
  start: CellPosition,
  end: CellPosition,
): CellPosition[] {
  const startDayIndex = DAY_NAMES.indexOf(start.day);
  const endDayIndex = DAY_NAMES.indexOf(end.day);
  const minDayIndex = Math.min(startDayIndex, endDayIndex);
  const maxDayIndex = Math.max(startDayIndex, endDayIndex);

  const minHour = Math.min(start.hour, end.hour);
  const maxHour = Math.max(start.hour, end.hour);

  const cells: CellPosition[] = [];
  for (let dayIdx = minDayIndex; dayIdx <= maxDayIndex; dayIdx++) {
    for (let hour = minHour; hour <= maxHour; hour++) {
      cells.push({ day: DAY_NAMES[dayIdx], hour });
    }
  }
  return cells;
}

export function useScheduleSelection({
  value,
  onChange,
  hours,
}: UseScheduleSelectionOptions) {
  const [selectionState, setSelectionState] = useState<SelectionState>({
    isSelecting: false,
    startCell: null,
    currentCell: null,
    selectionMode: null,
  });

  const gridRef = useRef<HTMLDivElement>(null);

  const isSelected = useCallback(
    (day: DayName, hour: number): boolean => {
      const timeSlot = formatTimeSlot(hour);
      return value[day].includes(timeSlot);
    },
    [value],
  );

  const getPreviewCells = useCallback((): CellPosition[] => {
    if (
      !selectionState.isSelecting ||
      !selectionState.startCell ||
      !selectionState.currentCell
    ) {
      return [];
    }
    return getSelectedCells(
      selectionState.startCell,
      selectionState.currentCell,
    );
  }, [selectionState]);

  const isPreview = useCallback(
    (day: DayName, hour: number): boolean => {
      const previewCells = getPreviewCells();
      return previewCells.some(
        (cell) => cell.day === day && cell.hour === hour,
      );
    },
    [getPreviewCells],
  );

  const applySelection = useCallback(() => {
    if (
      !selectionState.startCell ||
      !selectionState.currentCell ||
      !selectionState.selectionMode
    ) {
      return;
    }

    const cells = getSelectedCells(
      selectionState.startCell,
      selectionState.currentCell,
    );
    const newAvailability = { ...value };

    for (const cell of cells) {
      const timeSlot = formatTimeSlot(cell.hour);
      const daySlots = [...newAvailability[cell.day]];

      if (selectionState.selectionMode === "add") {
        if (!daySlots.includes(timeSlot)) {
          daySlots.push(timeSlot);
          daySlots.sort();
        }
      } else {
        const index = daySlots.indexOf(timeSlot);
        if (index !== -1) {
          daySlots.splice(index, 1);
        }
      }

      newAvailability[cell.day] = daySlots;
    }

    onChange(newAvailability);
  }, [selectionState, value, onChange]);

  const handleMouseDown = useCallback(
    (day: DayName, hour: number) => {
      const isCurrentlySelected = isSelected(day, hour);
      setSelectionState({
        isSelecting: true,
        startCell: { day, hour },
        currentCell: { day, hour },
        selectionMode: isCurrentlySelected ? "remove" : "add",
      });
    },
    [isSelected],
  );

  const handleMouseEnter = useCallback(
    (day: DayName, hour: number) => {
      if (selectionState.isSelecting) {
        setSelectionState((prev) => ({
          ...prev,
          currentCell: { day, hour },
        }));
      }
    },
    [selectionState.isSelecting],
  );

  const handleMouseUp = useCallback(() => {
    if (selectionState.isSelecting) {
      applySelection();
      setSelectionState({
        isSelecting: false,
        startCell: null,
        currentCell: null,
        selectionMode: null,
      });
    }
  }, [selectionState.isSelecting, applySelection]);

  const handleTouchStart = useCallback(
    (day: DayName, hour: number) => {
      const isCurrentlySelected = isSelected(day, hour);
      setSelectionState({
        isSelecting: true,
        startCell: { day, hour },
        currentCell: { day, hour },
        selectionMode: isCurrentlySelected ? "remove" : "add",
      });
    },
    [isSelected],
  );

  const getCellFromPoint = useCallback(
    (x: number, y: number): CellPosition | null => {
      const element = document.elementFromPoint(x, y);
      if (
        element?.hasAttribute("data-day") &&
        element?.hasAttribute("data-hour")
      ) {
        const day = element.getAttribute("data-day") as DayName;
        const hour = parseInt(element.getAttribute("data-hour")!, 10);
        if (DAY_NAMES.includes(day) && hours.includes(hour)) {
          return { day, hour };
        }
      }
      return null;
    },
    [hours],
  );

  // Global mouse up listener to handle mouse release outside the grid
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (selectionState.isSelecting) {
        applySelection();
        setSelectionState({
          isSelecting: false,
          startCell: null,
          currentCell: null,
          selectionMode: null,
        });
      }
    };

    document.addEventListener("mouseup", handleGlobalMouseUp);
    return () => document.removeEventListener("mouseup", handleGlobalMouseUp);
  }, [selectionState.isSelecting, applySelection]);

  // Touch move and end handlers
  useEffect(() => {
    if (!selectionState.isSelecting) return;

    const handleTouchMove = (e: TouchEvent) => {
      e.preventDefault(); // Prevent scrolling while selecting
      const touch = e.touches[0];
      const cell = getCellFromPoint(touch.clientX, touch.clientY);
      if (cell) {
        setSelectionState((prev) => ({
          ...prev,
          currentCell: cell,
        }));
      }
    };

    const handleTouchEnd = () => {
      applySelection();
      setSelectionState({
        isSelecting: false,
        startCell: null,
        currentCell: null,
        selectionMode: null,
      });
    };

    document.addEventListener("touchmove", handleTouchMove, { passive: false });
    document.addEventListener("touchend", handleTouchEnd);

    return () => {
      document.removeEventListener("touchmove", handleTouchMove);
      document.removeEventListener("touchend", handleTouchEnd);
    };
  }, [selectionState.isSelecting, applySelection, getCellFromPoint]);

  return {
    gridRef,
    selectionState,
    isSelected,
    isPreview,
    handlers: {
      onMouseDown: handleMouseDown,
      onMouseEnter: handleMouseEnter,
      onMouseUp: handleMouseUp,
      onTouchStart: handleTouchStart,
    },
  };
}
