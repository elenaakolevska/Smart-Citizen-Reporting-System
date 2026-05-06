import { Bell, LogOut } from "lucide-react";
import { useRole } from "@/context/RoleContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import logo from "@/assets/Urban.png";
export function Navbar() {
  const { role, userName, logout } = useRole();
  const navigate = useNavigate();
  const avatarInitial = userName.trim().charAt(0).toUpperCase() || "К";

  const roleLabels: Record<string, string> = {
    citizen: "Корисник",
    officer: "Службеник",
    admin: "Администратор",
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-6 sticky top-0 z-50">
      <div className="flex items-center gap-2">
        <img src={logo} className="h-14 w-auto" />
      </div>

      <div className="flex items-center gap-4">
        <span className="text-xs font-medium text-muted-foreground bg-secondary px-3 py-1.5 rounded-md">
          {roleLabels[role]}
        </span>
        <button className="p-2 rounded-lg hover:bg-secondary transition-colors relative">
          <Bell className="h-5 w-5 text-muted-foreground" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" />
        </button>
        <Avatar className="h-9 w-9">
          <AvatarFallback className="bg-primary/10 text-primary font-semibold text-sm">
            {avatarInitial}
          </AvatarFallback>
        </Avatar>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="text-destructive hover:text-destructive">
          <LogOut className="h-4 w-4 mr-1" /> Одјава
        </Button>
      </div>
    </header>
  );
}
