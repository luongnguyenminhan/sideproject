/* eslint-disable @typescript-eslint/no-explicit-any */
// AnimatedList.tsx - copy từ React Bits
import React from 'react';

interface AnimatedListProps<T> {
  items: T[];
  getKey: (item: T, idx: number) => string;
  renderItem: (item: T, idx: number) => React.ReactElement;
  animation?: 'slide-up' | 'fade';
  delayStep?: number; // giây
}

export function AnimatedList<T>({
  items,
  getKey,
  renderItem,
  animation = 'slide-up',
  delayStep = 0.05,
}: AnimatedListProps<T>) {
  return (
    <div>
      {items.map((item, idx) => {
        const element = renderItem(item, idx);
        return React.cloneElement(
          element,
          {
            key: getKey(item, idx),
            style: {
              ...(animation === 'slide-up'
                ? { transition: 'all 0.7s', transform: `translateY(${10 * (items.length - idx)}px)`, opacity: 1 }
                : { transition: 'opacity 0.7s', opacity: 1 }),
              animationDelay: `${idx * delayStep}s`,
              ...((element.props as any)?.style || {}),
            },
          } as any
        );
      })}
    </div>
  );
}

export default AnimatedList;
