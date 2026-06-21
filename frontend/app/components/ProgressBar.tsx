const STEPS: { key: string; label: string }[] = [
  { key: "task_received", label: "과제 수령" },
  { key: "exploring", label: "자료 탐색" },
  { key: "drafting", label: "작성" },
  { key: "under_review", label: "심사" },
  { key: "revising", label: "재작업" },
  { key: "completed", label: "완료" },
];

const ORDER = STEPS.map((s) => s.key);

export function ProgressBar({ state }: { state: string }) {
  const idx = ORDER.indexOf(state);
  return (
    <div className="steps">
      {STEPS.map((s, i) => {
        const cls =
          s.key === state ? "step active" : i < idx ? "step done" : "step";
        return (
          <span key={s.key} className={cls}>
            {i < idx ? "✓ " : ""}
            {s.label}
            {i < STEPS.length - 1 ? " ›" : ""}
          </span>
        );
      })}
    </div>
  );
}
