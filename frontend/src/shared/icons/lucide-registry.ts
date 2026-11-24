import {
  Activity,
  BookOpen,
  Bot,
  Bug,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Mic,
  Search,
  Settings,
  Smartphone,
  Square,
  StickyNote,
  Terminal,
  Wrench,
} from "lucide"

type IconNode = [string, Record<string, string | number>][]

const UsersAdmin: IconNode = [
  ["circle", { cx: 9.5, cy: 7.6, r: 3.3 }],
  ["path", { d: "M3.4 20.2c0-3.1 2.8-5.3 6.1-5.3s6.1 2.2 6.1 5.3" }],
  ["path", { d: "M16.3 4.9a3.2 3.2 0 0 1 0 6.3" }],
  ["path", { d: "M18.5 14.9c2.1.7 3.3 2.4 3.3 4.6" }],
]

const ModelChip: IconNode = [
  ["rect", { x: 6.4, y: 6.4, width: 11.2, height: 11.2, rx: 2.2 }],
  ["rect", { x: 10.2, y: 10.2, width: 3.6, height: 3.6, rx: 0.8 }],
  ["path", { d: "M9.2 3.1v3.3" }],
  ["path", { d: "M14.8 3.1v3.3" }],
  ["path", { d: "M9.2 17.6v3.3" }],
  ["path", { d: "M14.8 17.6v3.3" }],
  ["path", { d: "M3.1 9.2h3.3" }],
  ["path", { d: "M3.1 14.8h3.3" }],
  ["path", { d: "M17.6 9.2h3.3" }],
  ["path", { d: "M17.6 14.8h3.3" }],
]

export const lucideIconSubset = {
  Activity,
  BookOpen,
  Bot,
  Bug,
  ClipboardList,
  Crosshair,
  FileBarChart,
  GitBranch,
  Layers,
  LayoutDashboard,
  Mic,
  Search,
  Settings,
  Smartphone,
  Square,
  StickyNote,
  Terminal,
  Wrench,
  UsersAdmin,
  ModelChip,
}
