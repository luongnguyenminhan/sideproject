import * as React from "react"
import { cn } from "@/lib/utils"
import { Input, InputProps } from "./input"

interface InputWithIconProps extends InputProps {
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  onRightIconClick?: () => void
  onLeftIconClick?: () => void
}

const InputWithIcon = React.forwardRef<HTMLInputElement, InputWithIconProps>(
  ({ 
    className, 
    leftIcon, 
    rightIcon, 
    onLeftIconClick, 
    onRightIconClick,
    ...props 
  }, ref) => {
    return (
      <div className="relative">
        {leftIcon && (
          <div 
            className={cn(
              "absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground",
              onLeftIconClick && "cursor-pointer hover:text-foreground"
            )}
            onClick={onLeftIconClick}
          >
            {leftIcon}
          </div>
        )}
        
        <Input
          className={cn(
            leftIcon && "pl-10",
            rightIcon && "pr-10",
            className
          )}
          ref={ref}
          {...props}
        />
        
        {rightIcon && (
          <div 
            className={cn(
              "absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground",
              onRightIconClick && "cursor-pointer hover:text-foreground"
            )}
            onClick={onRightIconClick}
          >
            {rightIcon}
          </div>
        )}
      </div>
    )
  }
)

InputWithIcon.displayName = "InputWithIcon"

export { InputWithIcon } 