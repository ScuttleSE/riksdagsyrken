<script>
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { store } from '$lib/data.svelte.js';

	let { children } = $props();

	const nav = [
		['/', 'Översikt'],
		['/yrken/', 'Yrken'],
		['/sok/', 'Sök ledamot'],
		['/jamfor/', 'Jämför partier']
	];

	onMount(() => {
		store.theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
		store.load();
	});

	function toggleTheme() {
		store.theme = store.theme === 'dark' ? 'light' : 'dark';
		document.documentElement.classList.toggle('dark', store.theme === 'dark');
		try {
			localStorage.setItem('tema', store.theme);
		} catch {}
	}

	const path = $derived(page.url.pathname.slice(base.length) || '/');
</script>

<header class="sticky top-0 z-30 border-b border-[var(--border)] backdrop-blur-xl" style="background: color-mix(in srgb, var(--bg) 75%, transparent)">
	<div class="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
		<a href="{base}/" class="flex items-center gap-2.5">
			<span class="grid h-9 w-9 place-items-center rounded-xl text-lg text-white shadow-lg" style="background: linear-gradient(135deg, var(--accent), var(--accent2))">⚖</span>
			<span class="leading-tight">
				<span class="h-display block text-lg font-bold">Riksdagens yrken</span>
				<span class="block text-[11px] text-muted">Ledamöter i enkammarriksdagen 1971–</span>
			</span>
		</a>
		<nav class="ml-auto hidden gap-1 md:flex">
			{#each nav as [href, label]}
				<a
					href="{base}{href}"
					class="rounded-full px-3.5 py-1.5 text-sm font-medium transition {path === href || (href !== '/' && path.startsWith(href.slice(0, -1)))
						? 'bg-[color-mix(in_srgb,var(--accent)_16%,transparent)] text-accent'
						: 'text-muted hover:text-[var(--fg)]'}">{label}</a
				>
			{/each}
		</nav>
		<button onclick={toggleTheme} class="ml-auto rounded-full border border-[var(--border)] p-2 text-muted hover:text-[var(--fg)] md:ml-2" aria-label="Byt tema">
			{store.theme === 'dark' ? '☀️' : '🌙'}
		</button>
	</div>
	<nav class="flex gap-1 overflow-x-auto px-4 pb-2 md:hidden">
		{#each nav as [href, label]}
			<a href="{base}{href}" class="whitespace-nowrap rounded-full px-3 py-1 text-sm {path === href ? 'text-accent' : 'text-muted'}">{label}</a>
		{/each}
	</nav>
</header>

<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6">
	{#if store.error}
		<div class="card p-6 text-red-400">Kunde inte läsa data: {store.error}</div>
	{:else if !store.data}
		<div class="grid place-items-center py-32 text-muted">
			<div class="h-10 w-10 animate-spin rounded-full border-4 border-[var(--border)] border-t-[var(--accent)]"></div>
			<p class="mt-4">Laddar ledamöter…</p>
		</div>
	{:else}
		{@render children()}
	{/if}
</main>

<footer class="mx-auto max-w-7xl px-4 pb-10 pt-4 text-xs text-muted sm:px-6">
	Källa: <a class="underline" href="https://sv.wikipedia.org/wiki/Listor_%C3%B6ver_ledam%C3%B6ter_av_Sveriges_riksdag">Wikipedia – Listor över ledamöter av Sveriges riksdag</a>
	och Wikidata (CC BY-SA) samt <a class="underline" href="https://www.riksdagen.se/sv/dokument-och-lagar/riksdagens-oppna-data/">Riksdagens öppna data</a>.
	Yrken är hämtade ur riksdagens personuppgifter, listornas yrkeskolumn (1971–1988), Wikipedia och Wikidata, och grupperade automatiskt – fel kan förekomma.
	{#if store.data}Data hämtad {store.data.generated}.{/if}
</footer>
