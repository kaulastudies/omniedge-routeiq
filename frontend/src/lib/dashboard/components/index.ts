/**
 * Public API of the tournament dashboard component library.
 *
 * Portability notes:
 * - No router-specific imports. Safe to lift into Next.js / any React app.
 * - State lives in `../store` (Zustand). No context providers needed.
 * - Styling: Tailwind v4 semantic tokens declared in `src/styles.css`
 *   (--shell, --tile, --brand, --court, etc.). When porting, copy the
 *   :root token block and the two @utility helpers (font-display,
 *   shell-gradient) into your target app's CSS entry.
 * - Icons: react-icons/lu (Lucide subset).
 * - Charts: recharts.
 */
export { DashboardShell } from "./DashboardShell";
export { Sidebar } from "./Sidebar";
export { TopBar } from "./TopBar";
export { HeroCard } from "./HeroCard";
export { CourtCard } from "./CourtCard";
export { TeamAdminCard } from "./TeamAdminCard";
export { MostActiveTeamsCard } from "./MostActiveTeamsCard";
export { LiveViewsCard } from "./LiveViewsCard";
export { TotalTeamsCard, RegisteredCard, CompletionCard, ActiveMatchesCard } from "./StatCards";
export { TileCard } from "./TileCard";
export { RosetteChart } from "./RosetteChart";
export { Logo } from "./Logo";
