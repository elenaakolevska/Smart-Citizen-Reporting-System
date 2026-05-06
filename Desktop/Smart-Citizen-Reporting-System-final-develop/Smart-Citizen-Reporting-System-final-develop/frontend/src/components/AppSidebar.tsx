import {
  Home,
  FileText,
  PlusCircle,
  LayoutDashboard,
  ClipboardList,
  BarChart3,
  Settings,
  Map as MapIcon,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useRole } from "@/context/RoleContext";

interface NavItem {
  title: string;
  url: string;
  icon: React.ElementType;
}

const citizenNav: NavItem[] = [
  { title: "Почетна", url: "/", icon: Home },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Мои пријави", url: "/my-complaints", icon: FileText },
  { title: "Нова пријава", url: "/new-complaint", icon: PlusCircle },
];

const officerNav: NavItem[] = [
  { title: "Контролна табла", url: "/dashboard", icon: LayoutDashboard },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Доделени пријави", url: "/assigned-complaints", icon: ClipboardList },
];

const adminNav: NavItem[] = [
  { title: "Контролна табла", url: "/dashboard", icon: LayoutDashboard },
  { title: "Интерактивна мапа", url: "/public-map", icon: MapIcon },
  { title: "Управување со пријави", url: "/manage-complaints", icon: Settings },
  { title: "Аналитички преглед", url: "/analytics", icon: BarChart3 },
];

export function AppSidebar() {
  const { role } = useRole();

  const navItems =
    role === "citizen" ? citizenNav :
    role === "officer" ? officerNav :
    adminNav;

  return (
    <aside className="w-56 border-r bg-card flex flex-col min-h-[calc(100vh-4rem)] sticky top-16">
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.url}
            to={item.url}
            end={item.url === "/"}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
          >
            <item.icon className="h-4.5 w-4.5" />
            <span>{item.title}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
