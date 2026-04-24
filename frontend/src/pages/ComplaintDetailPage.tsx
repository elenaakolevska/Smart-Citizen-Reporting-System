import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ChevronLeft,
  MapPin,
  Calendar,
  Tag,
  History,
  Star,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { fetchReportById, rateReport, updateReportPriority } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import { useRole } from "@/context/RoleContext";
import {
  deriveTitle,
  formatDate,
  formatCoords,
  getStatusStyle,
  getPriorityStyle,
  formatPriority,
} from "@/lib/reportHelpers";
import { StatusTimeline } from "@/components/StatusTimeline";
import { CommentsSection } from "@/components/CommentsSection";
import { toast } from "sonner";

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { categoryLabel, statusLabel } = useLookups();
  const { role } = useRole();

  const [isRatingOpen, setIsRatingOpen] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState("");

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["reports", id],
    queryFn: () => fetchReportById(Number(id)),
    enabled: !!id,
  });

  const rateMutation = useMutation({
    mutationFn: ({ rating, comment }: { rating: number; comment: string }) =>
      rateReport(Number(id), rating, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", id] });
      setIsRatingOpen(false);
      toast.success("Ви благодариме на оцената!");
    },
    onError: () => {
      toast.error("Грешка при зачувување на оцената.");
    },
  });

  const priorityMutation = useMutation({
    mutationFn: (newPriority: string) => updateReportPriority(Number(id), newPriority),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", id] });
      toast.success("Приоритетот е ажуриран.");
    },
    onError: () => {
      toast.error("Грешка при ажурирање на приоритетот.");
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
        <div className="flex items-center justify-between">
          <Button variant="ghost" className="pl-0 hover:bg-transparent" onClick={() => navigate(-1)}>
            <ChevronLeft className="mr-2 h-4 w-4" /> Назад
          </Button>

          {/* CR-06: Citizen can rate closed reports */}
          {report.status_id === 5 && role === "citizen" && !report.rating && (
            <Button onClick={() => setIsRatingOpen(true)}>Оцени ја услугата</Button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <CardTitle className="text-2xl">{deriveTitle(report.description)}</CardTitle>
                      {/* CR-02: Priority Badge */}
                      <Badge variant="outline" className={getPriorityStyle(report.priority)}>
                        {formatPriority(report.priority)}
                      </Badge>
                    </div>
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
                <div className="flex flex-wrap gap-6">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Категорија:</span>
                    <Badge variant="secondary">{categoryLabel(report.category_id)}</Badge>
                  </div>

                  {/* CR-06: Average Rating display */}
                  {report.rating && (
                    <div className="flex items-center gap-2">
                      <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      <span className="text-sm font-medium">Оценка:</span>
                      <span className="text-sm font-bold">{report.rating}/5</span>
                      {report.rating_comment && (
                        <span className="text-xs text-muted-foreground italic">("{report.rating_comment}")</span>
                      )}
                    </div>
                  )}
                </div>

                {/* CR-02: Officer/Admin Priority Change */}
                {(role === "admin" || role === "officer") && (
                  <div className="pt-4 border-t space-y-3">
                    <h4 className="text-sm font-semibold flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-primary" /> Управување со приоритет
                    </h4>
                    <div className="flex items-center gap-3">
                      <Select
                        value={report.priority || "low"}
                        onValueChange={(val) => priorityMutation.mutate(val)}
                        disabled={priorityMutation.isPending}
                      >
                        <SelectTrigger className="w-40">
                          <SelectValue placeholder="Приоритет" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Низок</SelectItem>
                          <SelectItem value="medium">Среден</SelectItem>
                          <SelectItem value="high">Висок</SelectItem>
                          <SelectItem value="urgent">Итен</SelectItem>
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-muted-foreground">
                        Променете го приоритетот за побрзо решавање на итни случаи.
                      </p>
                    </div>
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

      {/* CR-06: Rating Dialog */}
      <Dialog open={isRatingOpen} onOpenChange={setIsRatingOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Оценете ја услугата</DialogTitle>
            <DialogDescription>
              Вашето мислење е важно за подобрување на ефикасноста на службите.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center justify-center gap-2 py-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className="focus:outline-none transition-transform hover:scale-110"
                >
                  <Star
                    className={`h-8 w-8 ${
                      star <= rating
                        ? "text-yellow-500 fill-yellow-500"
                        : "text-muted-foreground"
                    }`}
                  />
                </button>
              ))}
            </div>
            <div className="grid gap-2">
              <label htmlFor="comment" className="text-sm font-medium">
                Опционален коментар
              </label>
              <Textarea
                id="comment"
                placeholder="Споделете го вашето искуство..."
                value={ratingComment}
                onChange={(e) => setRatingComment(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsRatingOpen(false)}
              disabled={rateMutation.isPending}
            >
              Откажи
            </Button>
            <Button
              onClick={() => rateMutation.mutate({ rating, comment: ratingComment })}
              disabled={rating === 0 || rateMutation.isPending}
            >
              {rateMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Испрати
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
