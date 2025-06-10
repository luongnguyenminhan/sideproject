// ScrambledText.tsx - copy từ React Bits
import React, { JSX, useEffect, useRef, useState } from 'react';

interface ScrambledTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: string;
  speed?: number; // 0.1-1, càng nhỏ càng chậm
  scramble?: 'always' | 'once';
  as?: keyof JSX.IntrinsicElements;
  className?: string;
}

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

export const ScrambledText: React.FC<ScrambledTextProps> = ({
  children,
  speed = 0.5,
  scramble = 'once',
  as = 'span',
  className = '',
  ...rest
}) => {
  const [display, setDisplay] = useState(children);
  const [done, setDone] = useState(false);
  const frame = useRef(0);
  const tag = as;

  useEffect(() => {
    let raf: number;
    let iterations = 0;
    const scrambleText = () => {
      let revealed = '';
      let finished = true;
      for (let i = 0; i < children.length; i++) {
        if (iterations > i * (1 / speed)) {
          revealed += children[i];
        } else {
          revealed += CHARS[Math.floor(Math.random() * CHARS.length)];
          finished = false;
        }
      }
      setDisplay(revealed);
      if (!finished) {
        raf = requestAnimationFrame(scrambleText);
        iterations++;
      } else {
        setDone(true);
      }
    };
    if (scramble === 'always' || !done) {
      setDone(false);
      frame.current = 0;
      iterations = 0;
      scrambleText();
    } else {
      setDisplay(children);
    }
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line
  }, [children, speed, scramble]);

  return React.createElement(tag, { className, ...rest }, display);
};

export default ScrambledText;
