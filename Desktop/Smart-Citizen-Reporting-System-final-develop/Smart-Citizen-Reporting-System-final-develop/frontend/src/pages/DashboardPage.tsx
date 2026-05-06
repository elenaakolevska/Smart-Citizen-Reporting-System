import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchReports, updateReportStatus, updateReportCategory } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, deriveTitle, getPriorityLabel, getPriorityStyle, getStatusStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const ACTIVE_STATUS_NAMES = new Set([
  "active",
  "aktiven",
  "aktivna",
  "aktivni",
  "активен",
  "активна",
  "активно",
  "активни",
  "submitted",
  "in progress",
  "pending",
  "нов",
  "нова",
  "поднесен",
  "поднесена",
  "во тек",
  "на чекање",
]);

const RESOLVED_STATUS_NAMES = new Set([
  "resolved",
  "closed",
  "resen",
  "reshen",
  "решен",
  "решена",
  "решено",
  "решени",
  "затворен",
  "затворена",
  "затворено",
  "затворени",
]);

function normalizeStatusName(status: string): string {
  return status.trim().toLowerCase().replace(/[_-]/g, " ").replace(/\s+/g, " ");
}

function isActiveStatus(status: string): boolean {
  return ACTIVE_STATUS_NAMES.has(normalizeStatusName(status));
}

function isResolvedStatus(status: string): boolean {
  return RESOLVED_STATUS_NAMES.has(normalizeStatusName(status));
}

export default function DashboardPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { data: reports = [], isLoading, error } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });
  const { statusLabel, categoryLabel, statuses, categories } = useLookups();

  const statusMutation = useMutation({
    mutationFn: ({ reportId, status_id }: { reportId: string; status_id: number }) =>
      updateReportStatus(reportId, status_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Статусот е ажуриран." });
    },
    onError: (err: Error) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на статус.",
        variant: "destructive",
      });
    },
  });

  const categoryMutation = useMutation({
    mutationFn: ({ reportId, category_id }: { reportId: string; category_id: number }) =>
      updateReportCategory(reportId, category_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Категоријата е ажурирана." });
    },
    onError: (err: Error) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на категорија.",
        variant: "destructive",
      });
    },
  });

  const stats = useMemo(() => {
    const active = reports.filter((r) => isActiveStatus(statusLabel(r.status_id))).length;

    const resolved = reports.filter((r) => isResolvedStatus(statusLabel(r.status_id))).length;

    const urgent = reports.filter((r) => getPriorityLabel(r.priority) === "Итен").length;

    return {
      total: reports.length,
      active,
      resolved,
      urgent,
    };
  }, [reports, statusLabel]);

  const recentReports = [...reports]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10);

  const statCards = [
    { label: "Вкупно пријави", value: stats.total, icon: FileText, color: "text-primary" },
    { label: "Активни (во тек)", value: stats.active, icon: Clock, color: "text-warning" },
    { label: "Решени", value: stats.resolved, icon: CheckCircle, color: "text-success" },
    { label: "Итни случаи", value: stats.urgent, icon: AlertTriangle, color: "text-destructive" },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Контролна табла</h1>
          <p className="text-muted-foreground text-sm">
            Преглед, приоритизација и ефикасно решавање на граѓански пријави во реално време.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading && Array.from({ length: 4 }).map((_, idx) => (
            <Card key={`skeleton-${idx}`}>
              <CardContent className="py-5">
                <Skeleton className="h-4 w-2/3 mb-2" />
                <Skeleton className="h-8 w-1/3" />
              </CardContent>
            </Card>
          ))}
          {!isLoading && statCards.map((s) => (
            <Card key={s.label}>
              <CardContent className="py-5 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{s.label}</p>
                  <p className="text-2xl font-bold text-foreground">{s.value.toLocaleString()}</p>
                </div>
                <s.icon className={`h-8 w-8 ${s.color} opacity-70`} />
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Последни пријави</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {/* <th className="text-left py-3 px-2 font-medium">ID</th> */}
                    <th className="text-left py-3 px-2 font-medium">Наслов</th>
                    <th className="text-left py-3 px-2 font-medium">Категорија</th>
                    <th className="text-left py-3 px-2 font-medium">Статус</th>
                    <th className="text-left py-3 px-2 font-medium">Датум</th>
                    <th className="text-left py-3 px-2 font-medium">Приоритет</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted-foreground">Се вчитуваат пријавите...</td>
                    </tr>
                  )}
                  {!isLoading && recentReports.map((report) => {
                    let username = report.user_email ? report.user_email.split("@")[0] : report.user_id?.slice(0, 8);
                    let mkCategory = getCategoryMacedonianName(categoryLabel(report.category_id));
                    return (
                      <tr
                        key={report.id}
                        className="border-b last:border-0 hover:bg-secondary/50 transition-colors"
                      >
                        <td className="py-3 px-2">
                          <div className="font-medium text-foreground">{deriveTitle(report.description, 64)}</div>
                          <div className="text-xs text-muted-foreground">корисник {username}</div>
                        </td>
                        <td className="py-3 px-2">
                          <Select
                            value={report.category_id?.toString() ?? undefined}
                            onValueChange={(value) => {
                              const newCategoryId = Number(value);
                              if (newCategoryId === report.category_id) return;
                              categoryMutation.mutate({ reportId: report.id, category_id: newCategoryId });
                            }}
                            disabled={categoryMutation.isPending}
                          >
                            <SelectTrigger className="w-[140px] text-xs">
                              <SelectValue placeholder="Избери категорија" />
                            </SelectTrigger>
                            <SelectContent>
                              {categories.map((cat) => (
                                <SelectItem key={cat.id} value={cat.id.toString()}>
                                  {getCategoryMacedonianName(cat.name)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="py-3 px-2">
                          <Select
                            value={report.status_id?.toString() ?? undefined}
                            onValueChange={(value) => {
                              const newStatusId = Number(value);
                              if (newStatusId === report.status_id) return;
                              statusMutation.mutate({ reportId: report.id, status_id: newStatusId });
                            }}
                            disabled={statusMutation.isPending}
                          >
                            <SelectTrigger className="w-[140px] text-xs">
                              <SelectValue placeholder="Избери статус" />
                            </SelectTrigger>
                            <SelectContent>
                              {statuses.map((s) => (
                                <SelectItem key={s.id} value={s.id.toString()}>
                                  {s.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="py-3 px-2 text-muted-foreground">{formatDate(report.created_at)}</td>
                        <td className="py-3 px-2">
                          <Badge variant="outline" className={getPriorityStyle(report.priority)}>
                            {getPriorityLabel(report.priority)}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                  {!isLoading && !error && recentReports.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-muted-foreground">Нема пријави.</td>
                    </tr>
                  )}
                  {!isLoading && error && (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-destructive">Неуспешно вчитување на пријавите.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
