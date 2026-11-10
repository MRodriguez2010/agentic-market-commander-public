import type { LucideIcon } from "lucide-react";

export type ViewId = "cockpit" | "strategy" | "research" | "economics" | "audit" | "settings";

export interface TabItem {
  id: ViewId;
  label: string;
  icon: LucideIcon;
}

interface TabsProps {
  tabs: TabItem[];
  active: ViewId;
  onChange: (view: ViewId) => void;
}

export function Tabs({ tabs, active, onChange }: TabsProps): JSX.Element {
  return (
    <nav className="tabs" aria-label="Primary">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            className={active === tab.id ? "active" : ""}
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            aria-pressed={active === tab.id}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
