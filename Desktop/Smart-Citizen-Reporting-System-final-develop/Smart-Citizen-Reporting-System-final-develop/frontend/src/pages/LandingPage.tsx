import { FileText, CheckCircle, Users, ArrowRight, Shield, Building2, Megaphone } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import logo from "@/assets/Urban.png";

export default function LandingPage() {
  const navigate = useNavigate();

  const stats = [
    { icon: FileText, label: "Пријавени случаи", value: "1,240", color: "text-primary" },
    { icon: CheckCircle, label: "Решени проблеми", value: "890", color: "text-success" },
    { icon: Users, label: "Активни граѓани", value: "4,500+", color: "text-warning" },
  ];

  const categories = [
    { title: "Инфраструктура", desc: "Оштетени патишта, дупки на коловозот, расипано улично осветлување.", icon: Building2 },
    { title: "Комунални услуги", desc: "Проблеми со отпад, водоснабдување или парковско зеленило.", icon: Megaphone },
    { title: "Администрација", desc: "Барања за јавни услуги, бирократски проблеми.", icon: FileText },
    { title: "Безбедност", desc: "Непрописно паркирани возила, опасни објекти, јавно нарушување.", icon: Shield },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <header className="h-16 border-b bg-card flex items-center justify-between px-6 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <img src={logo} className="h-16 w-auto" />
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate("/login")}>Најава</Button>
          <Button onClick={() => navigate("/register")}>Регистрација</Button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 space-y-16 pb-16">
        {/* Hero */}
        <div className="text-center space-y-5 pt-16">
          <span className="inline-block text-xs font-semibold uppercase tracking-wider text-primary bg-primary/10 px-4 py-1.5 rounded-full">
            Систем за пријава на проблеми
          </span>
          <h1 className="text-4xl md:text-5xl font-extrabold text-foreground leading-tight">
            Подобра заедница<br />
            започнува со <span className="text-primary">Вас</span>
          </h1>
          <p className="text-muted-foreground max-w-xl mx-auto text-lg">
            UrbanCare овозможува едноставно и ефикасно пријавување на инфраструктурни и комунални проблеми.
            Придружете се и придонесете за побрзо решавање.
          </p>
          <div className="flex gap-3 justify-center pt-3">
            <Button onClick={() => navigate("/login")} size="lg">
              Најава <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button variant="outline" size="lg" onClick={() => navigate("/register")}>
              Регистрација
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats.map((s) => (
            <Card key={s.label} className="text-center">
              <CardContent className="pt-6 pb-4 space-y-2">
                <s.icon className={`h-8 w-8 mx-auto ${s.color}`} />
                <p className="text-3xl font-bold text-foreground">{s.value}</p>
                <p className="text-sm text-muted-foreground">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Categories */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-foreground text-center">Што можете да пријавите?</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {categories.map((c) => (
              <Card key={c.title} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-5 pb-4 flex gap-4 items-start">
                  <div className="p-2.5 rounded-lg bg-primary/10">
                    <c.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-1">{c.title}</h3>
                    <p className="text-sm text-muted-foreground">{c.desc}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* CTA */}
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="py-10 text-center space-y-3">
            <h2 className="text-2xl font-bold">Подготвени сте да направите промена?</h2>
            <p className="opacity-90">Придружете се на илјадници одговорни граѓани. Процесот трае помалку од 2 минути.</p>
            <Button variant="secondary" size="lg" onClick={() => navigate("/register")} className="mt-2">
              Поднесете ја вашата прва пријава
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <footer className="border-t bg-card py-6 text-center text-sm text-muted-foreground">
        © 2026 UrbanCare. Сите права се задржани.
      </footer>
    </div>
  );
}
