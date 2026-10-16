<script>
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { store, wikiUrl, NONE } from '$lib/data.svelte.js';
	import Avatar from '$lib/Avatar.svelte';

	const d = $derived(store.data);
	const m = $derived(d.byId.get(page.url.searchParams.get('id') ?? ''));
	const sources = { riksdagen: 'Riksdagen', lista: 'Riksdagslistan', wikipedia: 'Wikipedia', wikidata: 'Wikidata', manuell: 'Manuell' };
	const p = $derived(m ? d.partyMap[m.t.at(-1).p] : null);
</script>

<svelte:head><title>{m?.n ?? 'Ledamot'} – Riksdagens yrken</title></svelte:head>

{#if !m}
	<div class="card p-8 text-center text-muted">Hittade ingen ledamot. <a class="text-accent" href="{base}/sok/">Till sökningen</a></div>
{:else}
	<button class="mb-4 text-sm text-muted hover:text-accent" onclick={() => history.back()}>← Tillbaka</button>
	<div class="card fade-in overflow-hidden">
		<div class="h-24" style="background: linear-gradient(120deg, {p?.f ?? '#64748b'}, color-mix(in srgb, {p?.f ?? '#64748b'} 30%, transparent))"></div>
		<div class="-mt-12 flex flex-col gap-5 px-6 pb-6 sm:flex-row sm:items-end">
			{#key m.id}
				<Avatar {m} color={p?.f ?? '#64748b'} size="h-28 w-28" text="text-3xl" rounded="rounded-2xl" extra="border-4 border-[var(--bg)] shadow-xl ring-0" />
			{/key}
			<div class="flex-1">
				<h1 class="h-display text-3xl font-bold">{m.n}</h1>
				<p class="text-muted">
					{p?.n ?? 'Okänt parti'}{#if m.b} · född {m.b}{/if}{#if m.k} · {m.k}{/if}
				</p>
			</div>
			<div class="flex gap-2">
				{#if m.rd}
					<a href={m.rd} target="_blank" rel="noopener" class="rounded-full border border-[var(--border)] px-4 py-2 text-sm font-medium hover:text-accent">Riksdagen ↗</a>
				{/if}
				{#if wikiUrl(m)}
					<a href={wikiUrl(m)} target="_blank" rel="noopener" class="rounded-full border border-[var(--border)] px-4 py-2 text-sm font-medium hover:text-accent">Wikipedia ↗</a>
				{/if}
			</div>
		</div>
	</div>

	<div class="mt-6 grid gap-6 lg:grid-cols-3">
		<div class="card p-6 lg:col-span-2">
			<h2 class="label mb-3">Yrken</h2>
			{#if m.y.length}
				<div class="space-y-2">
					{#each m.y as y, i}
						<div class="flex flex-wrap items-center gap-3">
							<span class="text-lg font-semibold capitalize">{y.y}</span>
							<a href="{base}/yrken/?g={encodeURIComponent(y.g)}" class="chip on" style:--c={d.groupColor[y.g]}>
								<span class="dot" style:background={d.groupColor[y.g]}></span>{y.g}
							</a>
							{#if i === m.y.findIndex((x) => x.g === m.h)}<span class="text-xs text-accent">huvudyrke</span>{/if}
							<span class="ml-auto text-xs text-muted">källa: {sources[y.s]}</span>
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-muted">{NONE} – varken riksdagen eller Wikipedia anger något yrke utöver politiker.</p>
			{/if}
			{#if m.i}
				<h2 class="label mb-2 mt-6">Ur Wikipedia</h2>
				<p class="leading-relaxed text-[var(--fg)]/90">{m.i}</p>
			{/if}
		</div>

		<div class="card p-6">
			<h2 class="label mb-3">Mandatperioder ({m.t.length})</h2>
			<div class="mb-4 flex gap-0.5">
				{#each d.terms as t, i}
					{@const mt = m.t.find((x) => x.t === i)}
					<div
						class="h-6 flex-1 rounded-sm"
						style:background={mt ? d.partyMap[mt.p]?.f : 'color-mix(in srgb, var(--fg) 8%, transparent)'}
						title="{t.s}–{t.e}{mt ? ' · ' + mt.p : ''}"
					></div>
				{/each}
			</div>
			<ul class="space-y-2 text-sm">
				{#each m.t as t}
					<li class="flex items-center gap-2">
						<span class="dot" style:background={d.partyMap[t.p]?.f}></span>
						<span class="w-24 tabular-nums">{d.terms[t.t].s}–{d.terms[t.t].e}</span>
						<span class="flex-1 truncate text-muted">{t.vk}</span>
						{#if t.r === 'e'}<span class="text-xs text-muted" title="Ersättare eller tillkommen under perioden">ers.</span>{/if}
					</li>
				{/each}
			</ul>
		</div>
	</div>
{/if}
