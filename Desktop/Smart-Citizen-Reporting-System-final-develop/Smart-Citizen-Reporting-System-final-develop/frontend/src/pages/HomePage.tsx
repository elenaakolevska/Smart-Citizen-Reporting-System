import { AppLayout } from "@/components/AppLayout";
import { useRole } from "@/context/RoleContext";
import { FileText, CheckCircle, ArrowRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const { userName } = useRole();
  const navigate = useNavigate();

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="space-y-3 pt-4">
          <h1 className="text-3xl font-extrabold text-foreground">
            Добредојдовте, {userName}! 👋
          </h1>
          <p className="text-muted-foreground text-lg">
            Користете го системот UrbanCare за да пријавите проблеми во вашата заедница
            и следете го статусот на вашите пријави.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/new-complaint")}>
            <CardContent className="py-8 text-center space-y-3">
              <FileText className="h-10 w-10 mx-auto text-primary" />
              <h3 className="font-semibold text-foreground text-lg">Нова пријава</h3>
              <p className="text-sm text-muted-foreground">Поднесете нов проблем за вашата околина</p>
              <Button size="sm">
                Поднеси <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate("/my-complaints")}>
            <CardContent className="py-8 text-center space-y-3">
              <CheckCircle className="h-10 w-10 mx-auto text-success" />
              <h3 className="font-semibold text-foreground text-lg">Мои пријави</h3>
              <p className="text-sm text-muted-foreground">Прегледајте ги вашите поднесени пријави</p>
              <Button variant="outline" size="sm">
                Преглед <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
