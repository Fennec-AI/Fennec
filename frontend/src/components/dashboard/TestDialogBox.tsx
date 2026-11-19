import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Terminal,
    AlertTriangle,
    CheckCircle,
    Loader2,
} from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { usePentestContext } from '@/contexts/PentestContext';
import { targetApi, credentialApi, pentestApi } from '@/services/api';
import type { Target, Credential, JobResponse } from '@/types';

interface TestDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    prefillJobId?: string | null;
}

function hostOf(value: string): string {
    try {
        return new URL(value.includes('://') ? value : `https://${value}`).hostname.toLowerCase();
    } catch {
        return value.toLowerCase();
    }
}

export function TestDialog({ open, onOpenChange, prefillJobId }: TestDialogProps) {
    const navigate = useNavigate();

    // Form state
    const [selectedTargetId, setSelectedTargetId] = useState('');
    const [selectedCredentialId, setSelectedCredentialId] = useState('');
    const [method, setMethod] = useState<'turbo' | 'balanced' | 'deep'>('balanced');
    const [frequency, setFrequency] = useState<string>('none');
    const [localError, setLocalError] = useState('');
    const [originalJob, setOriginalJob] = useState<JobResponse | null>(null);
    const [prefillLoading, setPrefillLoading] = useState(false);
    const [credentialNeedsReview, setCredentialNeedsReview] = useState(false);
    const [started, setStarted] = useState(false);
    const pendingCredentialId = useRef<string | null>(null);

    // Data state
    const [targets, setTargets] = useState<Target[]>([]);
    const [credentials, setCredentials] = useState<Credential[]>([]);
    const [targetsLoading, setTargetsLoading] = useState(false);
    const [credentialsLoading, setCredentialsLoading] = useState(false);

    const {
        startStream,
        sessionId,
        connectionStatus,
        testStatus,
        error: streamError,
    } = usePentestContext();

    const isLoading =
        started && (connectionStatus === 'connecting' ||
        (connectionStatus === 'connected' && testStatus === 'running'));

    // Navigate when sessionId is set and we're connected (not on error)
    // Only fires while the dialog is open — prevents yanking the user back to
    // the status page when they navigate elsewhere with an active session.
    useEffect(() => {
        if (!open || !started) return;
        // As soon as the backend returns a job id (sessionId), the assessment
        // HAS started — close the dialog and jump to the live status page.
        // Previously this was gated on testStatus === 'running', which the OSS
        // event stream may never surface, leaving the button stuck on
        // "Starting...". Navigating on sessionId (absent an error) is reliable.
        if (sessionId && !streamError && connectionStatus !== 'error') {
            const timer = setTimeout(() => {
                onOpenChange(false);
                navigate(`/dashboard/status/${sessionId}`);
            }, 600);
            return () => clearTimeout(timer);
        }
    }, [open, started, sessionId, streamError, connectionStatus, navigate, onOpenChange]);

    // Reset state when dialog opens
    useEffect(() => {
        if (open) {
            setSelectedTargetId('');
            setSelectedCredentialId('');
            setMethod('balanced');
            setFrequency('none');
            setLocalError('');
            setCredentials([]);
            setOriginalJob(null);
            setCredentialNeedsReview(false);
            setStarted(false);
            pendingCredentialId.current = null;
        }
    }, [open]);

    // Load the Create choices and the original test before filling the form.
    useEffect(() => {
        if (!open) return;
        let active = true;
        setTargetsLoading(true);
        setPrefillLoading(Boolean(prefillJobId));
        Promise.all([
            targetApi.list(),
            prefillJobId ? pentestApi.getJob(prefillJobId) : Promise.resolve(null),
        ]).then(([availableTargets, job]) => {
            if (!active) return;
            setTargets(availableTargets);
            if (!job) return;
            setOriginalJob(job);
            if (['turbo', 'balanced', 'deep'].includes(job.method)) {
                setMethod(job.method as 'turbo' | 'balanced' | 'deep');
            }
            setFrequency(['daily', 'weekly', 'monthly'].includes(job.frequency || '')
                ? job.frequency! : 'none');
            const target = availableTargets.find(t => t.id === job.target_id)
                ?? availableTargets.find(t => hostOf(t.domain) === hostOf(job.target_url));
            if (!target) {
                setLocalError('O alvo original não está mais cadastrado. Cadastre-o para refazer o teste.');
                return;
            }
            pendingCredentialId.current = job.credential_id;
            setSelectedTargetId(target.id);
        }).catch(err => {
            if (active) setLocalError(err instanceof Error ? err.message : 'Não foi possível carregar o teste original.');
        }).finally(() => {
            if (active) { setTargetsLoading(false); setPrefillLoading(false); }
        });
        return () => { active = false; };
    }, [open, prefillJobId]);

    // Load credentials when target changes
    useEffect(() => {
        if (!selectedTargetId) {
            setCredentials([]);
            setSelectedCredentialId('');
            return;
        }
        let active = true;
        setCredentialsLoading(true);
        setSelectedCredentialId('');
        credentialApi
            .list(selectedTargetId)
            .then(available => {
                if (!active) return;
                setCredentials(available);
                const preferred = pendingCredentialId.current;
                pendingCredentialId.current = null;
                if (preferred) {
                    if (available.some(item => item.id === preferred)) {
                        setSelectedCredentialId(preferred);
                    } else {
                        setCredentialNeedsReview(true);
                        setLocalError('A credencial original não está mais disponível. Escolha uma credencial ou “None” para continuar.');
                    }
                }
            })
            .catch((err) => {
                if (!active) return;
                console.error('Failed to load credentials:', err);
                setCredentials([]);
                if (pendingCredentialId.current) {
                    pendingCredentialId.current = null;
                    setCredentialNeedsReview(true);
                    setLocalError('Não foi possível confirmar a credencial original. Selecione uma credencial antes de continuar.');
                }
            })
            .finally(() => { if (active) setCredentialsLoading(false); });
        return () => { active = false; };
    }, [selectedTargetId]);

    const handleStartTest = async () => {
        if (prefillJobId && !originalJob) {
            setLocalError('Não foi possível carregar a configuração original. Feche e abra o formulário novamente.');
            return;
        }
        if (credentialNeedsReview) {
            setLocalError('Escolha uma credencial antes de continuar.');
            return;
        }
        if (!selectedTargetId) {
            setLocalError('Please select a target domain');
            return;
        }

        const target = targets.find((t) => t.id === selectedTargetId);
        if (!target) {
            setLocalError('Selected target not found');
            return;
        }

        let targetUrl = originalJob && hostOf(originalJob.target_url) === hostOf(target.domain)
            ? originalJob.target_url : target.domain;
        if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
            targetUrl = `https://${targetUrl}`;
        }

        setLocalError('');
        // Pass the user's dialog selections through to the job creation request.
        // Without these, selected credentials / method / frequency were silently
        // dropped and the job ended up with credential_id=null every time.
        const freq = frequency && frequency !== 'none'
            ? (frequency as 'daily' | 'weekly' | 'monthly')
            : null;
        setStarted(true);
        await startStream(
            targetUrl,
            originalJob?.name ?? `Assessment - ${target.name}`,
            originalJob?.description ?? undefined,
            originalJob?.htli,
            {
                target_id: target.id,
                credential_id: selectedCredentialId && selectedCredentialId !== 'none'
                    ? selectedCredentialId : undefined,
                method,
                frequency: freq,
                mode: originalJob?.mode === 'white_box' ? 'white_box' : 'black_box',
                timeout_seconds: originalJob?.timeout_seconds,
            },
        );
    };

    const error = localError || (started ? streamError : null);
    const status =
        !started ? '' : connectionStatus === 'connecting'
            ? 'Initializing...'
            : connectionStatus === 'connected' && sessionId
                ? 'Test started! Redirecting...'
                : '';
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>{prefillJobId ? 'Refazer avaliação' : 'Configure Continuous Testing'}</DialogTitle>
                    <DialogDescription>
                        {prefillJobId
                            ? 'Revise as configurações do teste original antes de iniciar uma nova avaliação.'
                            : 'Set up the parameters of your penetration test which will be used to guide the AI agents.'}
                    </DialogDescription>
                </DialogHeader>

                <div className="flex flex-col gap-4 pt-2">
                    {prefillLoading && <p className="text-sm text-muted-foreground">Carregando configuração original…</p>}
                    {originalJob && <div className="rounded-md border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
                        <p className="font-medium text-foreground">Teste original: {originalJob.name}</p>
                        <p>Modo: {originalJob.mode} · Revisão humana: {originalJob.htli ? 'sim' : 'não'} · Timeout: {originalJob.timeout_seconds}s</p>
                        {originalJob.description && <p className="mt-1">Descrição: {originalJob.description}</p>}
                    </div>}
                    {/* Target Domain */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Target Domain
                        </label>
                        <Select
                            value={selectedTargetId}
                            onValueChange={(val) => {
                                pendingCredentialId.current = null;
                                setSelectedTargetId(val);
                                setLocalError('');
                                setCredentialNeedsReview(false);
                            }}
                            disabled={isLoading || prefillLoading}
                        >
                            <SelectTrigger>
                                <SelectValue
                                    placeholder={
                                        targetsLoading
                                            ? 'Loading targets...'
                                            : 'Select a target'
                                    }
                                />
                            </SelectTrigger>
                            <SelectContent>
                                {targets.map((t) => (
                                    <SelectItem key={t.id} value={t.id}>
                                        {t.name}
                                        <span className="ml-2 text-xs text-muted-foreground">
                                            ({t.domain})
                                        </span>
                                    </SelectItem>
                                ))}
                                {targets.length === 0 && !targetsLoading && (
                                    <div className="px-2 py-3 text-center text-sm text-muted-foreground">
                                        No targets found. Add one first.
                                    </div>
                                )}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Authentication Credentials */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Authentication Credentials{' '}
                            <span className="text-muted-foreground font-normal">(Optional)</span>
                        </label>
                        <Select
                            value={selectedCredentialId}
                            onValueChange={value => {
                                setSelectedCredentialId(value);
                                setCredentialNeedsReview(false);
                                setLocalError('');
                            }}
                            disabled={isLoading || prefillLoading || credentialsLoading || !selectedTargetId}
                        >
                            <SelectTrigger>
                                <SelectValue
                                    placeholder={
                                        !selectedTargetId
                                            ? 'Select a target first'
                                            : credentialsLoading
                                                ? 'Loading credentials...'
                                                : 'None'
                                    }
                                />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                {credentials.map((c) => (
                                    <SelectItem key={c.id} value={c.id}>
                                        {c.name}
                                        <span className="ml-2 text-xs text-muted-foreground">
                                            ({c.username})
                                        </span>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Method */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">Method</label>
                        <div className="grid grid-cols-3 gap-2">
                            {(['turbo', 'balanced', 'deep'] as const).map((m) => (
                                <button
                                    key={m}
                                    type="button"
                                    onClick={() => setMethod(m)}
                                    disabled={isLoading || prefillLoading}
                                    className={`flex flex-col items-center gap-1 rounded-md border p-3 text-sm transition-colors ${
                                        method === m
                                            ? 'border-primary bg-primary/10 text-primary'
                                            : 'border-border hover:bg-muted/50 text-muted-foreground'
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                    <span className="font-medium capitalize">{m}</span>
                                    <span className="text-[10px] text-muted-foreground">
                                        {m === 'turbo'
                                            ? 'Fast scan'
                                            : m === 'balanced'
                                                ? 'Recommended'
                                                : 'Thorough'}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Frequency */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Frequency{' '}
                            <span className="text-muted-foreground font-normal">(Optional)</span>
                        </label>
                        <Select
                            value={frequency}
                            onValueChange={setFrequency}
                            disabled={isLoading || prefillLoading}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="None" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                <SelectItem value="daily">Daily</SelectItem>
                                <SelectItem value="weekly">Weekly</SelectItem>
                                <SelectItem value="monthly">Monthly</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Start Button */}
                    <Button
                        onClick={handleStartTest}
                        disabled={isLoading || prefillLoading || targetsLoading || credentialsLoading || credentialNeedsReview || !selectedTargetId || Boolean(prefillJobId && !originalJob)}
                        className="w-full"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin mr-1" />
                                Starting...
                            </>
                        ) : (
                            <>
                                <Terminal className="h-4 w-4 mr-1" />
                                Start Assessment
                            </>
                        )}
                    </Button>

                    {/* Error */}
                    {error  && (
                        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                            <AlertTriangle className="h-4 w-4 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Status */}
                    {status && !error  && (
                        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-400">
                            <CheckCircle className="h-4 w-4 shrink-0" />
                            <span>{status}</span>
                            {sessionId && (
                                <Badge variant="outline" className="ml-auto text-xs">
                                    {sessionId.slice(0, 8)}...
                                </Badge>
                            )}
                        </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                        Only test systems you have permission to assess.
                    </p>
                </div>
            </DialogContent>
        </Dialog>
    );
}
