import { AppLayout } from "@/components/AppLayout";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MapPin, Calendar } from "lucide-react";
import { useState } from "react";
import { fetchReports, updateReportPriority, updateReportStatus, updateReportCategory, type PriorityValue } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { formatDate, formatCoords, deriveTitle, getStatusStyle, getPriorityLabel, getPriorityStyle, getCategoryMacedonianName } from "@/lib/reportHelpers";
import { useToast } from "@/hooks/use-toast";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function AssignedComplaintsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel, statuses, categories } = useLookups();
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: reports = [] } = useQuery({
    queryKey: ["reports"],
    queryFn: fetchReports,
  });

  const priorityMutation = useMutation({
    mutationFn: ({ reportId, priority }: { reportId: string; priority: PriorityValue }) =>
      updateReportPriority(reportId, priority),
    onSuccess: () => {
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

  const assigned = reports.filter((r) => r.status_id === 1 || r.status_id === 2);
  const filtered =
    statusFilter === "all"
      ? assigned
      : assigned.filter((r) => String(r.status_id) === statusFilter);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Доделени пријави</h1>
            <p className="text-muted-foreground text-sm">Пријави доделени на вас за преглед и решавање.</p>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Сите</SelectItem>
              <SelectItem value="1">Нова</SelectItem>
              <SelectItem value="2">Во тек</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          {filtered.map((r) => {
            const username = r.user_email ? r.user_email.split("@")[0] : r.user_id.slice(0, 8);
            return (
              <Card
                key={r.id}
                className="hover:shadow-sm transition-shadow"
              >
                <CardContent className="py-4 space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <h3 className="font-semibold text-foreground truncate">{deriveTitle(r.description)}</h3>
                      <Badge variant="outline" className={`${getStatusStyle(r.status_id)} flex-shrink-0`}>
                        {statusLabel(r.status_id)}
                      </Badge>
                      <Badge variant="secondary" className="flex-shrink-0">{categoryLabel(r.category_id)}</Badge>
                      <Badge variant="outline" className={`${getPriorityStyle(r.priority)} flex-shrink-0`}>
                        {getPriorityLabel(r.priority)}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                    {r.latitude != null && r.longitude != null && (
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{formatCoords(r.latitude, r.longitude)}</span>
                    )}
                    <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />{formatDate(r.created_at)}</span>
                    <span>корисник {username}</span>
                  </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <Select
                    value={r.priority ?? undefined}
                    onValueChange={(value) => {
                      const nextPriority = value as PriorityValue;
                      if (nextPriority === r.priority) return;
                      priorityMutation.mutate({ reportId: r.id, priority: nextPriority });
                    }}
                    disabled={priorityMutation.isPending}
                  >
                    <SelectTrigger className="w-[130px]">
                      <SelectValue placeholder="Приоритет" />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((option) => (
                        <SelectItem key={option} value={option}>{option}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={r.status_id?.toString() ?? undefined}
                    onValueChange={(value) => {
                      const newStatusId = Number(value);
                      if (newStatusId === r.status_id) return;
                      statusMutation.mutate({ reportId: r.id, status_id: newStatusId });
                    }}
                    disabled={statusMutation.isPending}
                  >
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Статус" />
                    </SelectTrigger>
                    <SelectContent>
                      {statuses.map((s) => (
                        <SelectItem key={s.id} value={s.id.toString()}>
                          {s.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select
                    value={r.category_id?.toString() ?? undefined}
                    onValueChange={(value) => {
                      const newCategoryId = Number(value);
                      if (newCategoryId === r.category_id) return;
                      categoryMutation.mutate({ reportId: r.id, category_id: newCategoryId });
                    }}
                    disabled={categoryMutation.isPending}
                  >
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Категорија" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id.toString()}>
                          {getCategoryMacedonianName(cat.name)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            Нема доделени пријави со избраниот филтер.
          </div>
        )}
      </div>
    </AppLayout>
  );
}
