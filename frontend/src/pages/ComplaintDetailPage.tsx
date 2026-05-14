import { useParams, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, MapPin, Calendar, Tag, History, AlertTriangle, Star, MessageCircle, Paperclip, FileText, ExternalLink } from "lucide-react";
import { fetchReportById, updateReportPriority, type PriorityValue, fetchRating, fetchReportAttachments } from "@/services/reports";
import { fetchCategoryRatings } from "@/services/analytics";
import { useLookups } from "@/hooks/useLookups";
import { deriveTitle, formatDate, formatCoords, getPriorityLabel, getPriorityStyle, getStatusStyle, isResolvedStatus } from "@/lib/reportHelpers";
import { StatusTimeline } from "@/components/StatusTimeline";
import { CommentsSection } from "@/components/CommentsSection";
import { RatingModal } from "@/components/RatingModal";
import { useRole } from "@/context/RoleContext";
import { useToast } from "@/hooks/use-toast";

const PRIORITY_OPTIONS: PriorityValue[] = ["Низок", "Среден", "Висок", "Итен"];

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { categoryLabel, statusLabel } = useLookups();
  const { role, userId } = useRole();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);

  const canEditPriority = role === "officer" || role === "admin";

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["reports", id],
    queryFn: () => fetchReportById(id as string),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.category_id == null ? 2000 : false),
    refetchIntervalInBackground: true,
  });

  const { data: rating } = useQuery({
    queryKey: ["rating", id],
    queryFn: () => fetchRating(id as string),
    enabled: !!id,
  });

  const { data: attachments } = useQuery({
    queryKey: ["attachments", id],
    queryFn: () => fetchReportAttachments(id as string),
    enabled: !!id,
  });

  const { data: categoryRatings } = useQuery({
    queryKey: ["categoryRatings"],
    queryFn: fetchCategoryRatings,
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
      
    );
  }

  if (error || !report) {
    return (
      
        <div className="text-center py-12">
          <p className="text-destructive font-semibold">Грешка при вчитување на пријавата.</p>
          <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>Назад</Button>
        </div>
      
    );
  }

  const historyEntries = report.history_entries
    .filter((h) => h.status_id !== null)
    .map((h) => ({
      id: h.id,
      status_id: h.status_id as number,
      created_at: h.created_at,
    }));

  const isResolved = isResolvedStatus(statusLabel(report.status_id));
  const isOwner = report.user_id === userId;
  const canRate = isResolved && isOwner && !rating;

  const avgCategoryRating = categoryRatings?.find((r) => r.category_id === report.category_id);

  return (
      <div className="space-y-6">
        <Button variant="ghost" className="pl-0 hover:bg-transparent" onClick={() => navigate(-1)} aria-label="Врати се назад">
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
                  <Badge className={getStatusStyle(statusLabel(report.status_id))}>{statusLabel(report.status_id)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">Опис</h4>
                  <p className="text-foreground whitespace-pre-wrap">{report.description}</p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                </div>

                {avgCategoryRating && (
                  <div className="flex items-center gap-2 pt-2 border-t mt-4">
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    <span className="text-sm font-medium">Просечна оцена за оваа категорија:</span>
                    <span className="text-sm font-bold">{avgCategoryRating.average_stars.toFixed(1)}</span>
                    <span className="text-xs text-muted-foreground">({avgCategoryRating.ratings_count} оцени)</span>
                  </div>
                )}

                {report.possible_duplicate_of != null && (
                  <div className="rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-900 dark:text-amber-100">
                    Оваа пријава е означена како можен дупликат на пријава: "{report.possible_duplicate_of_report?.description ?? report.possible_duplicate_of}".
                  </div>
                )}

                {attachments && attachments.length > 0 && (
                  <div className="space-y-2 pt-2 border-t">
                    <h4 className="font-semibold flex items-center gap-2">
                      <Paperclip className="h-4 w-4" /> Прилози ({attachments.length})
                    </h4>
                    <ul className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {attachments.map((a) => {
                        const isImage = a.content_type.startsWith("image/");
                        return (
                          <li key={a.id} className="border rounded-md p-2 bg-muted/20">
                            <a
                              href={a.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block"
                              aria-label={`Отвори ${a.original_filename}`}
                            >
                              {isImage ? (
                                <img
                                  src={a.file_url}
                                  alt={a.original_filename}
                                  className="h-28 w-full object-cover rounded"
                                  loading="lazy"
                                />
                              ) : (
                                <div className="h-28 w-full flex items-center justify-center text-muted-foreground">
                                  <FileText className="h-10 w-10" />
                                </div>
                              )}
                              <p className="text-xs mt-1 truncate flex items-center gap-1" title={a.original_filename}>
                                <ExternalLink className="h-3 w-3 shrink-0" />
                                <span className="truncate">{a.original_filename}</span>
                              </p>
                              <p className="text-[10px] text-muted-foreground">
                                {(a.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </a>
                          </li>
                        );
                      })}
                    </ul>
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
                      <SelectTrigger className="max-w-[220px]" aria-label="Промени приоритет">
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

            {/* Rating Section */}
            {isResolved && isOwner && (
              <Card className={rating ? "border-success/50 bg-success/5" : "border-primary/50 bg-primary/5"}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Star className={`h-5 w-5 ${rating ? "text-yellow-500 fill-yellow-500" : "text-primary"}`} />
                    {rating ? "Вашата оцена" : "Оценете го решавањето"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {rating ? (
                    <div className="space-y-3">
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <Star key={s} className={`h-6 w-6 ${rating.stars >= s ? "fill-yellow-400 text-yellow-400" : "text-muted"}`} />
                        ))}
                      </div>
                      {rating.comment && (
                        <div className="bg-background/50 p-3 rounded-md border text-sm italic">
                          <MessageCircle className="h-4 w-4 inline mr-2 text-muted-foreground" />
                          "{rating.comment}"
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground">Оценето на {formatDate(rating.created_at)}</p>
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                      <p className="text-sm text-muted-foreground max-w-md">
                        Оваа пријава е означена како решена. Вашата оцена ни помага да ги подобриме услугите за сите граѓани.
                      </p>
                      {canRate ? (
                        <Button onClick={() => setIsRatingModalOpen(true)} aria-label="Оцени ја пријавата">Оцени сега</Button>
                      ) : (
                        <p className="text-xs italic text-muted-foreground">За да ја оцените пријавата, мора да сте подносителот.</p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
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

      <RatingModal
        reportId={report.id}
        isOpen={isRatingModalOpen}
        onClose={() => setIsRatingModalOpen(false)}
      />
      </div>
  );
}
