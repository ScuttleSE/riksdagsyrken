<script>
	import { store } from './data.svelte.js';

	let { showMode = true, showParties = true } = $props();
	const d = $derived(store.data);

	function setA(v) {
		v = +v;
		store.range = [Math.min(v, store.range[1]), store.range[1]];
	}
	function setB(v) {
		v = +v;
		store.range = [store.range[0], Math.max(v, store.range[0])];
	}
	function toggleParty(c) {
		store.parties = store.parties.includes(c)
			? store.parties.filter((p) => p !== c)
			: [...store.parties, c];
	}
	const n = $derived(d ? d.terms.length - 1 : 1);
</script>

{#if d}
	<div class="card flex flex-col gap-5 p-5 lg:flex-row lg:items-center lg:gap-8">
		<div class="min-w-0 flex-1">
			<div class="mb-2 flex items-baseline justify-between">
				<span class="label">Tidsperiod</span>
				<span class="font-semibold tabular-nums text-accent">{store.termLabel}</span>
			</div>
			<div class="range-wrap">
				<div
					class="range-fill"
					style:left="{(store.range[0] / n) * 100}%"
					style:right="{100 - (store.range[1] / n) * 100}%"
				></div>
				<input type="range" min="0" max={n} value={store.range[0]} oninput={(e) => setA(e.target.value)} aria-label="Från mandatperiod" />
				<input type="range" min="0" max={n} value={store.range[1]} oninput={(e) => setB(e.target.value)} aria-label="Till mandatperiod" />
			</div>
			<div class="mt-1 flex justify-between text-xs text-muted tabular-nums">
				<span>{d.terms[0].s}</span>
				<button class="hover:text-accent" onclick={() => (store.range = [0, n])}>Hela perioden</button>
				<button class="hover:text-accent" onclick={() => (store.range = [n, n])}>Senaste</button>
				<span>{d.terms[n].e}</span>
			</div>
		</div>

		{#if showMode}
			<div>
				<div class="label mb-2">Räkna</div>
				<div class="seg">
					<button class:on={store.mode === 'huvud'} onclick={() => (store.mode = 'huvud')} title="Varje ledamot räknas en gång, under sitt första icke-politiska yrke">Huvudyrke</button>
					<button class:on={store.mode === 'alla'} onclick={() => (store.mode = 'alla')} title="En ledamot räknas under alla sina yrkesgrupper">Alla yrken</button>
				</div>
			</div>
		{/if}

		{#if showParties}
			<div class="lg:max-w-md">
				<div class="label mb-2">
					Parti {#if store.parties.length}<button class="ml-2 normal-case text-accent" onclick={() => (store.parties = [])}>rensa</button>{/if}
				</div>
				<div class="flex flex-wrap gap-1.5">
					{#each d.parties as p}
						<button
							class="chip"
							class:on={store.parties.includes(p.c)}
							style:--c={p.f}
							onclick={() => toggleParty(p.c)}
							title={p.n}
						>
							<span class="dot" style:background={p.f}></span>{p.c}
						</button>
					{/each}
				</div>
			</div>
		{/if}
	</div>
{/if}
