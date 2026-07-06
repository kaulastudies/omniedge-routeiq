/**
 * Circular "C" monogram inspired by the reference. Pure SVG, themeable via
 * `color` prop. The original mark belongs to the referenced designer; this is
 * an original geometric approximation.
 */
export function Logo({
  size = 32,
  color = "currentColor",
  className,
}: {
  size?: number;
  color?: string;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Logo"
    >
      <circle cx="20" cy="20" r="19" stroke={color} strokeWidth="1.5" />
      <path
        d="M28 14.5C26.2 12.2 23.3 10.8 20 10.8C14.9 10.8 10.8 14.9 10.8 20C10.8 25.1 14.9 29.2 20 29.2C23.3 29.2 26.2 27.8 28 25.5"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <circle cx="27.5" cy="20" r="1.6" fill={color} />
    </svg>
  );
}
