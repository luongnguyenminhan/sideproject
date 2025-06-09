// AnimatedList.tsx - copy từ React Bits
import React from 'react';

interface AnimatedListProps<T> {
  items: T[];
  getKey: (item: T, idx: number) => string;
  renderItem: (item: T, idx: number) => React.ReactNode;
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
      {items.map((item, idx) =>
        React.cloneElement(
          renderItem(item, idx) as React.ReactElement,
          {
            key: getKey(item, idx),
            style: {
              ...(animation === 'slide-up'
                ? { transition: 'all 0.7s', transform: `translateY(${10 * (items.length - idx)}px)`, opacity: 1 }
                : { transition: 'opacity 0.7s', opacity: 1 }),
              animationDelay: `${idx * delayStep}s`,
              ...(renderItem(item, idx) as any).props.style,
            },
          }
        )
      )}
    </div>
  );
}

export default AnimatedList;
