import { cn } from "../lib/utils";

export function Button({
  className,
  variant = "default",
  size = "md",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "destructive" | "outline" | "ghost" | "secondary";
  size?: "sm" | "md" | "lg";
}) {
  const base =
    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive:
      "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline:
      "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary:
      "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    ghost: "hover:bg-accent hover:text-accent-foreground",
  };
  const sizes = {
    sm: "h-8 px-3 text-xs",
    md: "h-9 px-4 py-2",
    lg: "h-10 px-6",
  };
  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props} />
  );
}

export function Badge({
  className,
  variant,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "secondary" | "destructive" | "outline";
}) {
  const base = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold";
  const variants = {
    default: "bg-primary text-primary-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    outline: "border-input",
  };
  return (
    <span
      className={cn(base, variants[variant ?? "default"], className)}
      {...props}
    />
  );
}

export function Card({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border bg-card text-card-foreground shadow", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}

export function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export function StatCard({
  title,
  value,
  delta,
  icon: Icon,
}: {
  title: string;
  value: React.ReactNode;
  delta?: string;
  icon?: React.ElementType;
}) {
  return (
    <Card className="p-5">
      <div className="flex flex-col gap-2">
        {Icon && <Icon className="h-5 w-5 text-muted-foreground" />}
        <p className="text-sm text-muted-foreground">{title}</p>
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-bold">{value}</span>
          {delta && <span className="text-xs text-muted-foreground">{delta}</span>}
        </div>
      </div>
    </Card>
  );
}
