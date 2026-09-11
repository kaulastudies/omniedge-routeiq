import { Logo } from "./Logo";
import type { RegionSlice } from "../store";

/**
 * Six-petal rosette chart — petal radius encodes percent, angular position
 * is fixed. Center hosts the brand mark.
 */
export function RosetteChart({ data }: { data: RegionSlice[] }) {
  const cx = 180;
  const cy = 180;
  const maxR = 130;
  const minR = 45;

  const slices = data.slice(0, 6).map((slice, i) => {
    const angle = (i / 6) * Math.PI * 2 - Math.PI / 2;
    const r = minR + (slice.percent / 40) * (maxR - minR);
    // Petal shape: rounded teardrop pointing outward
    const tipX = cx + Math.cos(angle) * r;
    const tipY = cy + Math.sin(angle) * r;
    const perp = angle + Math.PI / 2;
    const width = 42;
    const baseX1 = cx + Math.cos(perp) * width - Math.cos(angle) * 4;
    const baseY1 = cy + Math.sin(perp) * width - Math.sin(angle) * 4;
    const baseX2 = cx - Math.cos(perp) * width - Math.cos(angle) * 4;
    const baseY2 = cy - Math.sin(perp) * width - Math.sin(angle) * 4;
    const ctrl1X = cx + Math.cos(perp) * (width * 0.7) + Math.cos(angle) * r * 0.9;
    const ctrl1Y = cy + Math.sin(perp) * (width * 0.7) + Math.sin(angle) * r * 0.9;
    const ctrl2X = cx - Math.cos(perp) * (width * 0.7) + Math.cos(angle) * r * 0.9;
    const ctrl2Y = cy - Math.sin(perp) * (width * 0.7) + Math.sin(angle) * r * 0.9;

    const path = `M ${baseX1} ${baseY1} Q ${ctrl1X} ${ctrl1Y} ${tipX} ${tipY} Q ${ctrl2X} ${ctrl2Y} ${baseX2} ${baseY2} Z`;

    // Label position (outside petal)
    const labelR = r + 24;
    const lx = cx + Math.cos(angle) * labelR;
    const ly = cy + Math.sin(angle) * labelR;

    return { ...slice, path, lx, ly, i };
  });

  return (
    <div className="relative w-full">
      <svg viewBox="0 0 360 360" className="h-full w-full">
        <defs>
          <radialGradient id="petal" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="oklch(0.82 0.19 145)" stopOpacity="0.95" />
            <stop offset="60%" stopColor="oklch(0.78 0.18 140)" stopOpacity="0.55" />
            <stop offset="100%" stopColor="oklch(0.78 0.18 140)" stopOpacity="0.05" />
          </radialGradient>
          <radialGradient id="petal-hot" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="oklch(0.65 0.22 25)" stopOpacity="0.95" />
            <stop offset="70%" stopColor="oklch(0.7 0.2 25)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="oklch(0.7 0.2 25)" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Petals */}
        {slices.map((s) => (
          <path
            key={s.label}
            d={s.path}
            fill={s.i === 0 ? "url(#petal-hot)" : "url(#petal)"}
            stroke="oklch(0.5 0.2 30 / 0.15)"
            strokeWidth="0.5"
          />
        ))}

        {/* Center red core */}
        <circle cx={cx} cy={cy} r="26" fill="oklch(0.55 0.22 27)" />
        <circle cx={cx} cy={cy} r="18" fill="oklch(0.25 0.05 250)" />

        {/* Labels */}
        {slices.map((s) => (
          <g key={`l-${s.label}`}>
            <text
              x={s.lx}
              y={s.ly - 4}
              textAnchor="middle"
              fontSize="15"
              fontWeight="600"
              className="fill-tile-fg"
              fontFamily="var(--font-sans)"
            >
              {s.percent}%
            </text>
            <text
              x={s.lx}
              y={s.ly + 10}
              textAnchor="middle"
              fontSize="10"
              className="fill-tile-muted"
              fontFamily="var(--font-sans)"
            >
              {s.label}
            </text>
          </g>
        ))}
      </svg>

      {/* Center logo overlay */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <Logo size={22} color="#fff" />
      </div>
    </div>
  );
}
