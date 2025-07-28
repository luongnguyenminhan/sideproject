import { Spin } from "antd";
import React from "react";

interface LoadingSectionWrapperProps {
  isLoading: boolean;
  children?: React.ReactNode;
}

const LoadingSectionWrapper = (props: LoadingSectionWrapperProps) => {
  const { isLoading, children } = props;

  if (isLoading) {
    return (
      <div className="flex h-64 w-full items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return <>{children}</>;
};

export { LoadingSectionWrapper };
