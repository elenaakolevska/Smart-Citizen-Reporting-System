import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { formatDate } from "@/lib/reportHelpers";
import { addComment, type CommentRead } from "@/services/reports";
import { useRole } from "@/context/RoleContext";
import { Loader2, MessageSquare } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Props {
  reportId: string;
  comments: CommentRead[];
}

export function CommentsSection({ reportId, comments }: Props) {
  const { role } = useRole();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [text, setText] = useState("");

  const canComment = role === "officer" || role === "admin";

  const mutation = useMutation({
    mutationFn: (content: string) => addComment(reportId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", String(reportId)] });
      setText("");
      toast({ title: "Успешно!", description: "Коментарот е додаден." });
    },
    onError: (err: any) => {
      toast({
        title: "Грешка",
        description: err.message ?? "Грешка при додавање коментар.",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    mutation.mutate(trimmed);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-lg font-semibold">
        <MessageSquare className="h-5 w-5" /> Коментари
      </div>

      {comments.length === 0 ? (
        <p className="text-sm text-muted-foreground italic">Сè уште нема коментари.</p>
      ) : (
        <div className="space-y-4">
          {comments.map((c) => (
            <div key={c.id} className="rounded-lg border bg-muted/20 p-4 space-y-1 shadow-sm">
              <p className="text-sm text-foreground whitespace-pre-wrap">{c.content}</p>
              <div className="flex justify-between items-center text-[10px] text-muted-foreground">
                <span>Корисник: {c.user_id.slice(0, 8)}...</span>
                <span>{formatDate(c.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {canComment && (
        <div className="space-y-3 pt-4 border-t">
          <Textarea
            placeholder="Додадете официјален коментар или забелешка…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            disabled={mutation.isPending}
          />
          <div className="flex justify-end">
            <Button 
              size="sm" 
              onClick={handleSubmit} 
              disabled={!text.trim() || mutation.isPending}
            >
              {mutation.isPending && <Loader2 className="mr-2 h-3 w-3 animate-spin" />}
              Додади коментар
            </Button>
          </div>
        </div>
      )}
      
      {!canComment && (
        <p className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-md italic">
          Само службени лица и администратори можат да додаваат коментари.
        </p>
      )}
    </div>
  );
}
