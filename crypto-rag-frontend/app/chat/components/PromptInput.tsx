"use client";

import { Textarea } from "@/ui/components/textarea";
import { cn } from "@/lib/utils";
import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";

type PromptInputContextType = {
  isLoading: boolean;
  value: string;
  setValue: (value: string) => void;
  maxHeight: number | string;
  onSubmit?: () => void;
  disabled?: boolean;
};

const PromptInputContext = createContext<PromptInputContextType>({
  isLoading: false,
  value: "",
  setValue: () => {},
  maxHeight: 240,
  onSubmit: undefined,
  disabled: false,
});

function usePromptInput() {
  const context = useContext(PromptInputContext);
  if (!context) {
    throw new Error("usePromptInput must be used within a PromptInput");
  }
  return context;
}

type PromptInputProps = {
  isLoading?: boolean;
  value?: string;
  onValueChange?: (value: string) => void;
  maxHeight?: number | string;
  onSubmit?: () => void;
  children: React.ReactNode;
  className?: string;
};

function PromptInput({
  className,
  isLoading = false,
  maxHeight = 240,
  value,
  onValueChange,
  onSubmit,
  children,
}: PromptInputProps) {
  const [internalValue, setInternalValue] = useState(value || "");

  const handleChange = (newValue: string) => {
    setInternalValue(newValue);
    onValueChange?.(newValue);
  };

  return (
    <PromptInputContext.Provider
      value={{
        isLoading,
        value: value ?? internalValue,
        setValue: onValueChange ?? handleChange,
        maxHeight,
        onSubmit,
      }}
    >
      <div
        className={cn(
          "border-input bg-background rounded-3xl border p-2 shadow-xs",
          className
        )}
      >
        {children}
      </div>
    </PromptInputContext.Provider>
  );
}

export type PromptInputTextareaProps = {
  disableAutosize?: boolean;
  textareaRef?: React.RefObject<HTMLTextAreaElement>;
} & React.ComponentProps<typeof Textarea>;

function PromptInputTextarea({
  className,
  onKeyDown,
  disableAutosize = false,
  textareaRef: externalRef,
  ...props
}: PromptInputTextareaProps) {
  const { value, setValue, maxHeight, onSubmit, disabled } = usePromptInput();
  const internalRef = useRef<HTMLTextAreaElement>(null);

  // Use the external ref if provided, otherwise use internal
  const textareaRef = externalRef || internalRef;

  const updateHeight = useCallback(() => {
    if (disableAutosize || !textareaRef.current) return;

    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height =
      typeof maxHeight === "number"
        ? `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`
        : `min(${textareaRef.current.scrollHeight}px, ${maxHeight})`;
  }, [disableAutosize, textareaRef, maxHeight]);

  // Update height when value changes
  useEffect(() => {
    updateHeight();
  }, [value, updateHeight]);

  // Also update on window resize
  useEffect(() => {
    if (disableAutosize) return;

    const handleResize = () => updateHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [updateHeight, disableAutosize]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit?.();
    } else {
      // Ensure we resize on key events like backspace and delete
      // which might not trigger an immediate value change
      setTimeout(updateHeight, 0);
    }
    onKeyDown?.(e);
  };

  return (
    <Textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onKeyDown={handleKeyDown}
      className={cn(
        "text-white min-h-[80px] w-full resize-none border-none bg-transparent shadow-none outline-none focus-visible:ring-0 focus-visible:ring-offset-0",
        className
      )}
      rows={1}
      disabled={disabled}
      {...props}
    />
  );
}

type PromptInputActionsProps = React.HTMLAttributes<HTMLDivElement>;

function PromptInputActions({
  children,
  className,
  ...props
}: PromptInputActionsProps) {
  return (
    <div className={cn("flex items-center gap-2", className)} {...props}>
      {children}
    </div>
  );
}

export { PromptInput, PromptInputTextarea, PromptInputActions };
