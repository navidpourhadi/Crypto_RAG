import { cn } from "@/lib/utils";
import { Markdown } from "@/ui/components/Markdown";

export type MessageProps = {
  children: React.ReactNode;
  className?: string;
} & React.HTMLProps<HTMLDivElement>;

const Message = ({ children, className, ...props }: MessageProps) => (
  <div className={cn("flex gap-3", className)} {...props}>
    {children}
  </div>
);

export type MessageContentProps = {
  children: React.ReactNode;
  markdown?: boolean;
  className?: string;
} & React.ComponentProps<typeof Markdown> &
  React.HTMLProps<HTMLDivElement>;

const MessageContent = ({
  children,
  markdown = false,
  className,
  ...props
}: MessageContentProps) => {
  const classNames = cn("rounded-xl p-4", className);

  return markdown ? (
    <Markdown className={classNames} {...props}>
      {String(children)}
    </Markdown>
  ) : (
    <div className={classNames} {...props}>
      {children}
    </div>
  );
};

export { Message, MessageContent };
