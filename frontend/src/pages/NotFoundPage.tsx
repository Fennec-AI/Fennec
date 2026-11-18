import { Link, useNavigate } from "react-router-dom";

export default function NotFoundPage() {
    const navigate = useNavigate();

    const handleBack = () => {
        if (window.history.length > 1) {
            navigate(-1);
            return;
        }
        navigate("/");
    };

    return (
        <main className="min-h-screen bg-[color:var(--color-dark-bg)] text-[color:var(--color-text-primary)]">
            <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
                <p className="text-sm font-medium uppercase tracking-[0.35em] text-[color:var(--color-text-secondary)]">
                    Fennec Security
                </p>
                <h1 className="mt-6 text-7xl font-semibold tracking-tight sm:text-8xl">
                    404
                </h1>
                <p className="mt-4 text-xl font-medium text-[color:var(--color-text-primary)] sm:text-2xl">
                    Page not found
                </p>
                <p className="mt-3 text-base text-[color:var(--color-text-secondary)] sm:text-lg">
                    The link you followed may be broken, or the page may have moved.
                </p>
                <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
                    <Link
                        to="/"
                        className="inline-flex h-7 items-center rounded-[4px] border border-border bg-ds-sunken px-3 text-[11px] font-semibold text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg"
                    >
                        Back to home
                    </Link>
                    <button
                        type="button"
                        onClick={handleBack}
                        className="inline-flex h-7 items-center rounded-[4px] border border-border bg-ds-sunken px-3 text-[11px] font-semibold text-ds-fg-muted hover:border-ds-border-strong hover:bg-ds-panel-hover hover:text-ds-fg"
                    >
                        Go back
                    </button>
                </div>
            </div>
        </main>
    );
}
