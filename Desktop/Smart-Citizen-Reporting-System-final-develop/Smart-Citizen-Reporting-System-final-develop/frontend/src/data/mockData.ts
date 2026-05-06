export interface Complaint {
  id: string;
  title: string;
  category: string;
  status: "new" | "in_progress" | "pending" | "resolved" | "rejected";
  date: string;
  priority: "high" | "medium" | "low";
  location: string;
  description: string;
  citizen: string;
}

export const complaints: Complaint[] = [
  {
    id: "CP-1024",
    title: "Оштетен асфалт и дупки",
    category: "Инфраструктура",
    status: "in_progress",
    date: "2024-05-15",
    priority: "high",
    location: "ул. Партизански Одреди, Скопје",
    description: "Голема дупка на средината на коловозот која претставува опасност за возилата.",
    citizen: "Марко Петров",
  },
  {
    id: "CP-1025",
    title: "Расипана улична светилка",
    category: "Комунални услуги",
    status: "new",
    date: "2024-05-14",
    priority: "medium",
    location: "Населба Аеродром, Скопје",
    description: "Уличните светилки на целиот ред не работат веќе три дена.",
    citizen: "Ана Стојанова",
  },
  {
    id: "CP-1026",
    title: "Нелегално фрлање отпад зад зградите",
    category: "Комунални услуги",
    status: "resolved",
    date: "2024-05-10",
    priority: "low",
    location: "ул. Македонија, Битола",
    description: "Насобрано големо количество на кабаст отпад и градежен шут.",
    citizen: "Игор Николов",
  },
  {
    id: "CP-1027",
    title: "Графити на споменик",
    category: "Комунални услуги",
    status: "new",
    date: "2024-05-15",
    priority: "medium",
    location: "Центар, Скопје",
    description: "Вандализам на јавен споменик во градскиот парк.",
    citizen: "Елена Ристеска",
  },
  {
    id: "CP-1028",
    title: "Непрописно паркирани возила",
    category: "Безбедност",
    status: "in_progress",
    date: "2024-05-13",
    priority: "high",
    location: "ул. Иво Лола Рибар, Тетово",
    description: "Возила паркирани на тротоар кои го блокираат движењето на пешаците.",
    citizen: "Дарко Митев",
  },
  {
    id: "CP-1029",
    title: "Расипана клупа во парк",
    category: "Инфраструктура",
    status: "rejected",
    date: "2024-05-09",
    priority: "low",
    location: "Градски Парк, Скопје",
    description: "Вандализирана опрема во детскиот парк.",
    citizen: "Марија Коцева",
  },
];
export interface User {
  id: string;
  name: string;
  email: string;
  role: "citizen" | "officer" | "admin";
  status: "active" | "inactive";
  dateJoined: string;
}

export const mockUsers: User[] = [
  { id: "U-001", name: "Марко Петров", email: "marko@mail.mk", role: "citizen", status: "active", dateJoined: "2024-01-10" },
  { id: "U-002", name: "Ана Стојанова", email: "ana@mail.mk", role: "officer", status: "active", dateJoined: "2024-02-15" },
  { id: "U-003", name: "Игор Николов", email: "igor@mail.mk", role: "citizen", status: "active", dateJoined: "2024-03-20" },
  { id: "U-004", name: "Елена Ристеска", email: "elena@mail.mk", role: "citizen", status: "inactive", dateJoined: "2024-01-05" },
  { id: "U-005", name: "Дарко Митев", email: "darko@mail.mk", role: "officer", status: "active", dateJoined: "2024-04-01" },
  { id: "U-006", name: "Админ Корисник", email: "admin@urbancare.mk", role: "admin", status: "active", dateJoined: "2023-12-01" },
];

export const categories = [
  "Инфраструктура",
  "Комунални услуги",
  "Администрација",
  "Безбедност",
];

export const dashboardStats = {
  totalComplaints: 1248,
  activeComplaints: 312,
  resolvedThisMonth: 84,
  urgentCases: 12,
};

export const analyticsStats = {
  totalComplaints: 1100,
  resolvedCases: 720,
  avgResolutionTime: "3.6 дена",
  activeCitizens: 4250,
};