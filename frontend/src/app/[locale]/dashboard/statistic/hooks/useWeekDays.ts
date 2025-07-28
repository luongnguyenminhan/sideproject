import dayjs from 'dayjs';
import { useMemo } from 'react';

const useWeekDays = () => {
  return useMemo(() => {
    const currentDate = dayjs();
    const startOfWeek =
      currentDate.day() === 0
        ? currentDate.day(-6).startOf('day')
        : currentDate.day(1).startOf('day');
    const daysInWeek = 7;
    const labels: string[] = [];
    const displayLabels: string[] = [];
    const dayNames: string[] = [];

    for (let day = 0; day < daysInWeek; day++) {
      const date = startOfWeek.add(day, 'day');
      labels.push(date.format('DD/MM/YYYY'));
      displayLabels.push(date.format('DD'));
      dayNames.push(date.format('dddd'));
    }

    return { labels, displayLabels, dayNames };
  }, []);
};

export { useWeekDays };
