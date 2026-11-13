export type ThemeId = "system" | "light" | "dark" | "paper" | "terminal" | "ocean";

export interface ThemeOption {
  id: ThemeId;
  label: string;
  description: string;
  swatches: [string, string, string];
}

export const THEMES: ThemeOption[] = [
  {
    id: "system",
    label: "System",
    description: "Follows OS light or dark",
    swatches: ["oklch(0.99 0 0)", "oklch(0.145 0 0)", "oklch(0.55 0 0)"],
  },
  {
    id: "light",
    label: "Light",
    description: "Clean sans · Neutral light",
    swatches: ["oklch(0.99 0 0)", "oklch(0.205 0 0)", "oklch(0.90 0 0)"],
  },
  {
    id: "dark",
    label: "Dark",
    description: "Clean sans · Neutral dark",
    swatches: ["oklch(0.145 0 0)", "oklch(0.92 0 0)", "oklch(0.28 0 0)"],
  },
  {
    id: "paper",
    label: "Paper",
    description: "Editorial serif · Warm cream",
    swatches: ["oklch(0.968 0.012 85)", "oklch(0.38 0.095 38)", "oklch(0.865 0.02 80)"],
  },
  {
    id: "terminal",
    label: "Terminal",
    description: "Mono · Sharp 0px · Phosphor",
    swatches: ["oklch(0.115 0.012 160)", "oklch(0.76 0.17 150)", "oklch(0.34 0.06 154)"],
  },
  {
    id: "ocean",
    label: "Ocean",
    description: "Soft rounded · Slate & cyan",
    swatches: ["oklch(0.165 0.028 248)", "oklch(0.74 0.135 205)", "oklch(0.31 0.038 242)"],
  },
];

const STORAGE_KEY = "webagent:theme";
const VALID_IDS = new Set<string>(THEMES.map((t) => t.id));

function isThemeId(value: string | null | undefined): value is ThemeId {
  return Boolean(value && VALID_IDS.has(value));
}

function getInitialTheme(): ThemeId {
  try {
    const saved = typeof localStorage !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (isThemeId(saved)) return saved;
  } catch {
    // Ignore storage access errors
  }

  const envDefault = (
    import.meta as ImportMeta & { env?: Record<string, string | undefined> }
  ).env?.VITE_DEFAULT_THEME;
  if (isThemeId(envDefault)) return envDefault;

  return "system";
}

function applyTheme(id: ThemeId): void {
  if (typeof document === "undefined") return;
  if (id === "system") {
    document.documentElement.dataset.theme = "system";
  } else {
    document.documentElement.dataset.theme = id;
  }
}

class ThemeStore {
  current = $state<ThemeId>(getInitialTheme());

  constructor() {
    applyTheme(this.current);
  }

  setTheme(id: ThemeId): void {
    this.current = id;
    applyTheme(id);
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {
      // Ignore storage write errors
    }
  }
}

export const themeStore = new ThemeStore();
