import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRole, UserRole } from "@/context/RoleContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import logo from "@/assets/Urban.png";

interface LoginPageProps {
  mode?: "login" | "register";
}

export default function LoginPage({ mode = "login" }: LoginPageProps) {
  const navigate = useNavigate();
  const { login, register } = useRole();
  const [activeTab, setActiveTab] = useState<"login" | "register">(mode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole | "">("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!role) {
      setErrorMessage(
        activeTab === "login"
          ? "Изберете улога за најава."
          : "Изберете улога за новата сметка.",
      );
      return;
    }

    try {
      setIsSubmitting(true);

      if (activeTab === "login") {
        await login(email, password, role as UserRole);
        navigate("/");
      } else {
        const result = await register(email, password, role as UserRole);

        if (result.emailConfirmationRequired) {
          setSuccessMessage("Проверете ја вашата е-пошта за потврда, па потоа најавете се.");
          setActiveTab("login");
        } else {
          navigate("/");
        }
      }
    } catch (error: any) {
      setErrorMessage(error?.message ?? "Настана грешка. Обидете се повторно.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const roleLabels: Record<UserRole, string> = {
    citizen: "Корисник",
    officer: "Службеник",
    admin: "Администратор",
  };

  return (
    <div className="min-h-screen bg-secondary/30 flex flex-col">
      {/* Navbar */}
      <header className="h-16 border-b bg-card flex items-center justify-between px-6">
        <button onClick={() => navigate("/")} className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <img src={logo} className="h-16 w-auto" />
          </div>
        </button>
      </header>

      <div className="flex-1 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-1">
            <CardTitle className="text-2xl">
              {activeTab === "login" ? "Најава" : "Регистрација"}
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              {activeTab === "login"
                ? "Пристапете до вашиот профил за да ги следите вашите пријави."
                : "Креирајте сметка за да почнете со пријавување проблеми."}
            </p>
          </CardHeader>
          <CardContent>
            {/* Tabs */}
            <div className="flex rounded-lg bg-secondary p-1 mb-6">
              <button
                onClick={() => setActiveTab("login")}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === "login"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Најава
              </button>
              <button
                onClick={() => setActiveTab("register")}
                className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === "register"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Регистрација
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Е-пошта *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="vasa@posta.mk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Лозинка *</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                {activeTab === "login" && (
                  <button type="button" className="text-xs text-primary hover:underline">
                    Заборавена лозинка?
                  </button>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Улога *</Label>
                <Select value={role} onValueChange={(val) => setRole(val as UserRole)}>
                  <SelectTrigger id="role">
                    <SelectValue
                      placeholder={
                        activeTab === "login"
                          ? "Изберете улога за најава"
                          : "Изберете улога"
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(roleLabels) as UserRole[]).map((r) => (
                      <SelectItem key={r} value={r}>{roleLabels[r]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {errorMessage && (
                <p className="text-sm text-destructive">{errorMessage}</p>
              )}

              {successMessage && (
                <p className="text-sm text-emerald-600">{successMessage}</p>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting || !role}
              >
                {activeTab === "login" ? "Најави се" : "Регистрирај се"}
              </Button>
            </form>

            <p className="text-center text-xs text-muted-foreground mt-6">
              Со продолжување, се согласувате со нашите{" "}
              <span className="text-primary cursor-pointer hover:underline">Услови за користење</span>.
            </p>
          </CardContent>
        </Card>
      </div>

      <footer className="border-t bg-card py-4 text-center text-xs text-muted-foreground">
        © 2026 UrbanCare. Сите права се задржани.
      </footer>
    </div>
  );
}
