import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, MapPin, Calendar, Tag, History, AlertTriangle } from "lucide-react";
import { fetchReportById, updateReportPriority, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, formatCoords, getPriorityLabel, getPriorityStyle, getStatusStyle } from "@/lib/reportHelpers";
import { StatusTimeline } from "@/components/StatusTimeline";
import { CommentsSection } from "@/components/CommentsSection";
import { useRole } from "@/context/RoleContext";
import { useToast } from "@/hooks/use-toast";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { categoryLabel, statusLabel } = useLookups();
  const { role } = useRole();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const canEditPriority = role === "officer" || role === "admin";

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["reports", id],
    queryFn: () => fetchReportById(id as string),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.category_id == null ? 2000 : false),
    refetchIntervalInBackground: true,
  });

  const priorityMutation = useMutation({
    mutationFn: (priority: PriorityValue) => {
      if (!report?.id) {
        throw new Error("Report is not loaded yet.");
      }
      return updateReportPriority(report.id, priority);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", id] });
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast({ title: "Успешно", description: "Приоритетот е ажуриран." });
    },
    onError: (err: Error) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Неуспешно ажурирање на приоритет.",
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-32" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <Card><CardContent className="p-6 space-y-4"><Skeleton className="h-8 w-3/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-full" /></CardContent></Card>
            </div>
            <div className="space-y-6">
              <Card><CardContent className="p-6 space-y-4"><Skeleton className="h-6 w-1/2" /><Skeleton className="h-20 w-full" /></CardContent></Card>
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (error || !report) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-destructive font-semibold">Грешка при вчитување на пријавата.</p>
          <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>Назад</Button>
        </div>
      </AppLayout>
    );
  }

  const historyEntries = report.history_entries
    .filter((h) => h.status_id !== null)
    .map((h) => ({
      id: h.id,
      status_id: h.status_id as number,
      created_at: h.created_at,
    }));

  return (
    <AppLayout>
      <div className="space-y-6">
        <Button variant="ghost" className="pl-0 hover:bg-transparent" onClick={() => navigate(-1)}>
          <ChevronLeft className="mr-2 h-4 w-4" /> Назад
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl">{deriveTitle(report.description)}</CardTitle>
                    <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><Calendar className="h-4 w-4" /> {formatDate(report.created_at)}</span>
                      {report.latitude && report.longitude && (
                        <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {formatCoords(report.latitude, report.longitude)}</span>
                      )}
                    </div>
                  </div>
                  <Badge className={getStatusStyle(report.status_id)}>{statusLabel(report.status_id)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">Опис</h4>
                  <p className="text-foreground whitespace-pre-wrap">{report.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Категорија:</span>
                  <Badge variant="secondary">{categoryLabel(report.category_id)}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Приоритет:</span>
                  <Badge variant="outline" className={getPriorityStyle(report.priority)}>
                    {getPriorityLabel(report.priority)}
                  </Badge>
                </div>
                {report.possible_duplicate_of != null && (
                  <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-900 dark:text-amber-100">
                    Оваа пријава е означена како можен дупликат на пријава #{report.possible_duplicate_of}.
                  </div>
                )}
                {canEditPriority && (
                  <div className="space-y-2 rounded-md border p-3 bg-muted/20">
                    <p className="text-sm font-medium">Промени приоритет</p>
                    <Select
                      value={report.priority ?? undefined}
                      onValueChange={(value) => {
                        const nextPriority = value as PriorityValue;
                        if (nextPriority === report.priority) return;
                        priorityMutation.mutate(nextPriority);
                      }}
                      disabled={priorityMutation.isPending}
                    >
                      <SelectTrigger className="max-w-[220px]">
                        <SelectValue placeholder="Избери приоритет" />
                      </SelectTrigger>
                      <SelectContent>
                        {PRIORITY_OPTIONS.map((option) => (
                          <SelectItem key={option} value={option}>{option}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="h-5 w-5" /> Историја на статус
                </CardTitle>
              </CardHeader>
              <CardContent>
                <StatusTimeline entries={historyEntries} />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <CommentsSection reportId={report.id} comments={report.comments} />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
