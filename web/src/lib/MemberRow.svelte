<script>
	import { base } from '$app/paths';
	import { store, termSpan, lastParty } from './data.svelte.js';

	let { m, highlight = null } = $props();
	const d = $derived(store.data);
	const p = $derived(d.partyMap[lastParty(m)]);
</script>

<a href="{base}/ledamot/?id={encodeURIComponent(m.id)}" class="group flex items-center gap-3 rounded-xl px-2 py-2 transition hover:bg-[color-mix(in_srgb,var(--fg)_5%,transparent)]">
	{#if m.img}
		<img src={m.img} alt="" loading="lazy" class="h-9 w-9 flex-none rounded-full object-cover ring-2" style:--tw-ring-color={p?.f ?? '#888'} />
	{:else}
		<span class="grid h-9 w-9 flex-none place-items-center rounded-full text-xs font-bold text-white" style:background={p?.f ?? '#64748b'}>
			{m.n.split(' ').map((s) => s[0]).slice(0, 2).join('')}
		</span>
	{/if}
	<span class="min-w-0 flex-1">
		<span class="block truncate text-sm font-medium group-hover:text-accent">{m.n}</span>
		<span class="block truncate text-xs text-muted">
			<span class="font-semibold" style:color={p?.f}>{p?.c ?? ''}</span>
			· {termSpan(m, d.terms)}
			{#if m.y.length}· {m.y.filter((y) => !highlight || y.g === highlight).concat(m.y.filter((y) => highlight && y.g !== highlight)).map((y) => y.y).slice(0, 3).join(', ')}{/if}
		</span>
	</span>
</a>
