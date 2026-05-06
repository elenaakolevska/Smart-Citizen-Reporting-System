import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { createReport } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import LocationPicker from "@/components/LocationPicker";
import { getCategoryMacedonianName } from "@/lib/reportHelpers";

export default function NewComplaintPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { categories } = useLookups();

  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (description.length < 20) {
      toast({
        title: "Грешка при валидација",
        description: "Внесете најмалку 20 карактери за описот.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    try {
      const report = await createReport({
        description,
        latitude: lat,
        longitude: lng,
        category_id: category ? Number(category) : null,
      });

      toast({ title: "Успешно!", description: "Вашата пријава е успешно поднесена." });

      if (report.possible_duplicate_of != null) {
        toast({
          title: "Можен дупликат",
          description: `Оваа пријава може да е дупликат на пријава #${report.possible_duplicate_of}.`,
        });
      }

      navigate(`/complaints/${report.id}`);
    } catch (err: any) {
      setError(err.message ?? "Грешка при поднесување на пријавата.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Нова пријава</h1>
          <p className="text-muted-foreground text-sm">Пополнете ги деталите подолу за да пријавите проблем во вашата заедница.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Детали за проблемот</CardTitle>
              <p className="text-sm text-muted-foreground">Обидете се да бидете што попрецизни при описот на ситуацијата.</p>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Category */}
              <div className="space-y-2">
                <Label htmlFor="category">Категорија (опционално)</Label>
                <Select value={category} onValueChange={setCategory}>
                  <SelectTrigger id="category"><SelectValue placeholder="Изберете категорија" /></SelectTrigger>
                  <SelectContent>
                    {categories.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>{getCategoryMacedonianName(c.name)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground italic">Ако не изберете, системот ќе се обиде автоматски да ја одреди категоријата.</p>
              </div>

              {/* Description */}
              <div className="space-y-2">
                <Label htmlFor="description">Детален опис *</Label>
                <Textarea
                  id="description"
                  placeholder="Опишете го проблемот овде... На пример: Има голема дупка на средината на патот која ги оштетува возилата."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={5}
                />
                <p className="text-xs text-muted-foreground italic">Минимум 20 карактери.</p>
              </div>

              {/* Location picker */}
              <div className="space-y-2">
                <Label>Локација (опционално)</Label>
                <p className="text-xs text-muted-foreground">Кликнете на мапата за да ја означите локацијата на проблемот.</p>
                <LocationPicker lat={lat} lng={lng} onChange={(la, ln) => { setLat(la); setLng(ln); }} />
                {lat != null && lng != null && (
                  <p className="text-xs text-muted-foreground">
                    Координати: {lat.toFixed(5)}, {lng.toFixed(5)}
                    <Button type="button" variant="link" className="text-xs ml-2 p-0 h-auto" onClick={() => { setLat(null); setLng(null); }}>
                      Отстрани
                    </Button>
                  </p>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 text-destructive text-sm">
                  <AlertTriangle className="h-4 w-4" />
                  {error}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => navigate(-1)} disabled={submitting}>
                  Откажи
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Поднеси пријава
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </div>
    </AppLayout>
  );
}
