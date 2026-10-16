<script>
	import { onMount, tick } from 'svelte';
	import { page } from '$app/state';
	import { store, countGroups, groupsOf, NONE, pct } from '$lib/data.svelte.js';
	import Filters from '$lib/Filters.svelte';
	import MemberRow from '$lib/MemberRow.svelte';

	const d = $derived(store.data);
	const sel = $derived(store.selected);
	const counts = $derived(countGroups(sel, store.mode).sort((a, b) => (a[0] === NONE) - (b[0] === NONE)));
	let open = $state(new Set());
	let limit = $state({});

	const byGroup = $derived.by(() => {
		const map = new Map();
		for (const m of sel) for (const g of groupsOf(m, store.mode)) {
			if (!map.has(g)) map.set(g, []);
			map.get(g).push(m);
		}
		return map;
	});

	function titles(g) {
		const c = new Map();
		for (const m of byGroup.get(g) ?? []) for (const y of m.y) if (y.g === g) c.set(y.y, (c.get(y.y) ?? 0) + 1);
		return [...c.entries()].sort((a, b) => b[1] - a[1]);
	}

	function toggle(g) {
		const s = new Set(open);
		s.has(g) ? s.delete(g) : s.add(g);
		open = s;
	}

	onMount(async () => {
		const g = page.url.searchParams.get('g');
		if (g) {
			open = new Set([g]);
			await tick();
			document.getElementById(`g-${g}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	});
</script>

<svelte:head><title>Yrkesgrupper – Riksdagens yrken</title></svelte:head>

<h1 class="h-display mb-2 text-4xl font-bold">Yrkesgrupper</h1>
<p class="mb-6 max-w-2xl text-muted">
	Ledamöterna grupperade efter yrke. Klicka på en grupp för att se vilka som ingår och vilka yrkestitlar gruppen består av.
</p>

<div class="mb-6"><Filters /></div>

<div class="space-y-3">
	{#each counts as [g, n] (g)}
		{@const isOpen = open.has(g)}
		<div id="g-{g}" class="card scroll-mt-28 overflow-hidden">
			<button class="flex w-full items-center gap-4 p-4 text-left sm:p-5" onclick={() => toggle(g)}>
				<span class="h-10 w-1.5 flex-none rounded-full" style:background={d.groupColor[g]}></span>
				<span class="min-w-0 flex-1">
					<span class="block font-semibold">{g}</span>
					<span class="mt-0.5 block truncate text-xs text-muted">
						{#if g === NONE}Inget yrke angivet utöver politiker{:else}{titles(g).slice(0, 6).map(([t]) => t).join(' · ')}{/if}
					</span>
				</span>
				<span class="hidden w-40 sm:block"><span class="bar-bg block h-2"><span class="block h-full rounded-full" style="width:{(100 * n) / counts[0][1]}%; background:{d.groupColor[g]}"></span></span></span>
				<span class="w-20 text-right">
					<span class="block font-bold tabular-nums">{n}</span>
					<span class="block text-xs text-muted tabular-nums">{pct(n, sel.length)}</span>
				</span>
				<span class="text-muted transition-transform {isOpen ? 'rotate-90' : ''}">›</span>
			</button>
			{#if isOpen}
				{@const ms = byGroup.get(g) ?? []}
				{@const lim = limit[g] ?? 60}
				<div class="fade-in border-t border-[var(--border)] px-4 pb-4 sm:px-5">
					{#if g !== NONE}
						<div class="flex flex-wrap gap-1.5 py-3">
							{#each titles(g) as [t, c]}
								<span class="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs"><span class="capitalize">{t}</span> <span class="text-muted">{c}</span></span>
							{/each}
						</div>
					{/if}
					<div class="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
						{#each ms.slice(0, lim) as m (m.id)}
							<MemberRow {m} highlight={g} />
						{/each}
					</div>
					{#if ms.length > lim}
						<button class="mt-3 text-sm font-medium text-accent" onclick={() => (limit = { ...limit, [g]: lim + 120 })}>
							Visa fler ({ms.length - lim} kvar)
						</button>
					{/if}
				</div>
			{/if}
		</div>
	{/each}
</div>
