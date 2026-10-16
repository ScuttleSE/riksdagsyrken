<script>
	import Fuse from 'fuse.js';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import { store, NONE } from '$lib/data.svelte.js';
	import Filters from '$lib/Filters.svelte';
	import MemberRow from '$lib/MemberRow.svelte';

	const d = $derived(store.data);
	let q = $state('');
	let group = $state('');
	let vk = $state('');
	let gender = $state('');
	let limit = $state(90);
	let ready = $state(false);

	const fuse = $derived(
		new Fuse(d.members, {
			keys: [
				{ name: 'n', weight: 3 },
				{ name: 'y.y', weight: 2 },
				{ name: 'y.g', weight: 1 },
				{ name: 't.vk', weight: 0.5 }
			],
			threshold: 0.3,
			ignoreLocation: true
		})
	);

	const valkretsar = $derived([...new Set(d.members.flatMap((m) => m.t.map((t) => t.vk)).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'sv')));

	const results = $derived.by(() => {
		const base = q.trim() ? fuse.search(q.trim()).map((r) => r.item) : d.members;
		return base.filter((m) => {
			const ts = store.termsInRange(m);
			if (!ts.length) return false;
			if (group === NONE ? m.y.length : group && !m.y.some((y) => y.g === group)) return false;
			if (vk && !ts.some((t) => t.vk === vk)) return false;
			if (gender && m.k !== gender) return false;
			return true;
		});
	});

	onMount(() => {
		q = page.url.searchParams.get('q') ?? '';
		group = page.url.searchParams.get('g') ?? '';
		ready = true;
	});

	$effect(() => {
		if (!ready) return;
		const u = new URL(location.href);
		q ? u.searchParams.set('q', q) : u.searchParams.delete('q');
		group ? u.searchParams.set('g', group) : u.searchParams.delete('g');
		replaceState(u, {});
		limit = 90;
	});
</script>

<svelte:head><title>Sök ledamot – Riksdagens yrken</title></svelte:head>

<h1 class="h-display mb-2 text-4xl font-bold">Sök ledamot</h1>
<p class="mb-6 text-muted">Sök på namn, yrke eller valkrets. Sökningen tål stavfel.</p>

<div class="relative mb-4">
	<svg class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
	<!-- svelte-ignore a11y_autofocus -->
	<input class="input" placeholder="T.ex. Olof Palme, lärare, lantbrukare, Malmö…" bind:value={q} autofocus />
</div>

<div class="mb-4"><Filters showMode={false} /></div>

<div class="mb-4 flex flex-wrap items-center gap-3">
	<select class="select" bind:value={group}>
		<option value="">Alla yrkesgrupper</option>
		{#each [...d.groups, NONE] as g}<option>{g}</option>{/each}
	</select>
	<select class="select max-w-[16rem]" bind:value={vk}>
		<option value="">Alla valkretsar</option>
		{#each valkretsar as v}<option>{v}</option>{/each}
	</select>
	<select class="select" bind:value={gender}>
		<option value="">Alla kön</option>
		<option value="kvinna">Kvinnor</option>
		<option value="man">Män</option>
	</select>
	<span class="ml-auto text-sm text-muted"><b class="text-[var(--fg)] tabular-nums">{results.length}</b> träffar</span>
</div>

<div class="card p-3 sm:p-4">
	{#if results.length === 0}
		<p class="p-8 text-center text-muted">Inga ledamöter matchar sökningen.</p>
	{:else}
		<div class="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
			{#each results.slice(0, limit) as m (m.id)}
				<MemberRow {m} highlight={group || null} />
			{/each}
		</div>
		{#if results.length > limit}
			<div class="pt-3 text-center">
				<button class="rounded-full border border-[var(--border)] px-4 py-1.5 text-sm font-medium text-accent" onclick={() => (limit += 150)}>Visa fler</button>
			</div>
		{/if}
	{/if}
</div>
