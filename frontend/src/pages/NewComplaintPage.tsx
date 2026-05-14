import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, Loader2, FileText, X, Upload } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { createReport, uploadReportAttachment } from "@/services/reports";
import { useLookups } from "@/hooks/useLookups";
import LocationPicker from "@/components/LocationPicker";
import { getCategoryMacedonianName } from "@/lib/reportHelpers";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;
const MAX_FILES = 5;
const ALLOWED_TYPES = new Set(["image/jpeg", "image/jpg", "image/png", "application/pdf"]);
const ALLOWED_EXT_PATTERN = /\.(jpe?g|png|pdf)$/i;

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
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<Record<string, string>>({});
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const next: Record<string, string> = {};
    for (const f of files) {
      if (f.type.startsWith("image/")) {
        next[`${f.name}:${f.size}`] = URL.createObjectURL(f);
      }
    }
    setPreviews(next);
    return () => {
      Object.values(next).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [files]);

  const handleFilesSelected = (selected: FileList | null) => {
    if (!selected || selected.length === 0) return;

    const incoming = Array.from(selected);
    const accepted: File[] = [];
    const rejected: string[] = [];

    for (const f of incoming) {
      const typeOk = ALLOWED_TYPES.has(f.type) || ALLOWED_EXT_PATTERN.test(f.name);
      if (!typeOk) {
        rejected.push(`${f.name} — неподдржан формат`);
        continue;
      }
      if (f.size > MAX_FILE_SIZE_BYTES) {
        rejected.push(`${f.name} — над 5 MB`);
        continue;
      }
      if (f.size === 0) {
        rejected.push(`${f.name} — празна датотека`);
        continue;
      }
      accepted.push(f);
    }

    if (rejected.length > 0) {
      toast({
        title: "Некои датотеки беа отфрлени",
        description: rejected.join("; "),
        variant: "destructive",
      });
    }

    setFiles((prev) => {
      const merged = [...prev];
      for (const f of accepted) {
        const dup = merged.find((m) => m.name === f.name && m.size === f.size);
        if (!dup) merged.push(f);
      }
      if (merged.length > MAX_FILES) {
        toast({
          title: "Премногу датотеки",
          description: `Дозволени се најмногу ${MAX_FILES} прилози.`,
          variant: "destructive",
        });
        return merged.slice(0, MAX_FILES);
      }
      return merged;
    });

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (key: string) => {
    setFiles((prev) => prev.filter((f) => `${f.name}:${f.size}` !== key));
  };

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

      // Upload attachments after the report is persisted. Failures are non-fatal:
      // the report is already created, so we surface a warning and continue.
      if (files.length > 0) {
        const results = await Promise.allSettled(
          files.map((f) => uploadReportAttachment(report.id, f)),
        );
        const failed = results
          .map((r, i) => (r.status === "rejected" ? files[i].name : null))
          .filter((name): name is string => name != null);
        if (failed.length > 0) {
          toast({
            title: "Дел од приложените слики не се качија",
            description: failed.join(", "),
            variant: "destructive",
          });
        }
      }

      navigate(`/complaints/${report.id}`);
    } catch (err: any) {
      setError(err.message ?? "Грешка при поднесување на пријавата.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
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
                  aria-required="true"
                  aria-describedby="description-hint"
                />
                <p id="description-hint" className="text-xs text-muted-foreground italic">Минимум 20 карактери.</p>
              </div>

              {/* Location picker */}
              <div className="space-y-2">
                <Label id="location-label">Локација (опционално)</Label>
                <p className="text-xs text-muted-foreground">Кликнете на мапата за да ја означите локацијата на проблемот.</p>
                <LocationPicker 
                  lat={lat} 
                  lng={lng} 
                  onChange={(la, ln) => { setLat(la); setLng(ln); }} 
                />
                {lat != null && lng != null && (
                  <p className="text-xs text-muted-foreground" aria-live="polite">
                    Координати: {lat.toFixed(5)}, {lng.toFixed(5)}
                    <Button 
                      type="button" 
                      variant="link" 
                      className="text-xs ml-2 p-0 h-auto" 
                      onClick={() => { setLat(null); setLng(null); }}
                      aria-label="Отстрани ја избраната локација"
                    >
                      Отстрани
                    </Button>
                  </p>
                )}
              </div>

              {/* Attachments */}
              <div className="space-y-2">
                <Label htmlFor="attachments">Прилози (опционално)</Label>
                <p className="text-xs text-muted-foreground">JPG, PNG или PDF. До 5 датотеки, секоја до 5 MB.</p>
                <input
                  ref={fileInputRef}
                  id="attachments"
                  type="file"
                  multiple
                  accept="image/jpeg,image/jpg,image/png,application/pdf"
                  className="hidden"
                  onChange={(e) => handleFilesSelected(e.target.files)}
                  disabled={submitting}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={submitting || files.length >= MAX_FILES}
                  aria-label="Изберете прилози"
                >
                  <Upload className="mr-2 h-4 w-4" />
                  Избери датотеки {files.length > 0 ? `(${files.length}/${MAX_FILES})` : ""}
                </Button>

                {files.length > 0 && (
                  <ul className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2" aria-label="Избрани прилози">
                    {files.map((f) => {
                      const key = `${f.name}:${f.size}`;
                      const preview = previews[key];
                      return (
                        <li key={key} className="relative border rounded-md p-2 bg-muted/20">
                          <button
                            type="button"
                            onClick={() => removeFile(key)}
                            className="absolute top-1 right-1 rounded-full bg-background/80 border p-0.5 hover:bg-destructive hover:text-destructive-foreground"
                            aria-label={`Отстрани ${f.name}`}
                            disabled={submitting}
                          >
                            <X className="h-3 w-3" />
                          </button>
                          {preview ? (
                            <img
                              src={preview}
                              alt={f.name}
                              className="h-24 w-full object-cover rounded"
                            />
                          ) : (
                            <div className="h-24 w-full flex items-center justify-center text-muted-foreground">
                              <FileText className="h-8 w-8" />
                            </div>
                          )}
                          <p className="text-xs mt-1 truncate" title={f.name}>{f.name}</p>
                          <p className="text-[10px] text-muted-foreground">
                            {(f.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </li>
                      );
                    })}
                  </ul>
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
  );
}
