<script>
	import { store, groupsOf } from '$lib/data.svelte.js';
	import Chart from '$lib/Chart.svelte';
	import Filters from '$lib/Filters.svelte';

	const d = $derived(store.data);
	let ta = $state(0);
	let tb = $state(store.data.terms.length - 1);

	const heat = $derived.by(() => {
		const [a, b] = store.range;
		const groups = d.groups;
		const parties = d.parties.filter((p) => p.c !== '-');
		const counts = new Map(parties.map((p) => [p.c, { n: 0, g: new Map() }]));
		for (const m of d.members) {
			if (!m.y.length) continue;
			const ps = new Set(m.t.filter((t) => t.t >= a && t.t <= b).map((t) => t.p));
			const gs = groupsOf(m, store.mode);
			for (const pc of ps) {
				const c = counts.get(pc);
				if (!c) continue;
				c.n++;
				for (const g of gs) c.g.set(g, (c.g.get(g) ?? 0) + 1);
			}
		}
		const active = parties.filter((p) => counts.get(p.c).n > 0);
		const data = [];
		active.forEach((p, x) =>
			groups.forEach((g, y) => {
				const c = counts.get(p.c);
				data.push([x, y, +((100 * (c.g.get(g) ?? 0)) / c.n).toFixed(1), c.g.get(g) ?? 0, c.n]);
			})
		);
		return { active, groups, data };
	});

	const heatOption = $derived({
		grid: { left: 8, right: 16, top: 8, bottom: 60, containLabel: true },
		tooltip: {
			formatter: (p) =>
				`<b>${heat.active[p.value[0]].n}</b><br>${heat.groups[p.value[1]]}: <b>${p.value[2]} %</b><br>${p.value[3]} av ${p.value[4]} ledamöter`
		},
		xAxis: { type: 'category', data: heat.active.map((p) => p.c), splitArea: { show: false } },
		yAxis: { type: 'category', data: heat.groups, inverse: true, axisLabel: { width: 200, overflow: 'truncate' } },
		visualMap: {
			dimension: 2,
			min: 0,
			max: Math.max(10, ...heat.data.map((x) => x[2])),
			calculable: true,
			orient: 'horizontal',
			left: 'center',
			bottom: 0,
			itemWidth: 12,
			textStyle: { color: store.theme === 'dark' ? '#cbd5e1' : '#334155' },
			inRange: { color: store.theme === 'dark' ? ['#111827', '#6d28d9', '#db2777', '#fbbf24'] : ['#f8fafc', '#c4b5fd', '#db2777', '#9a3412'] }
		},
		series: [
			{
				type: 'heatmap',
				data: heat.data,
				label: { show: true, formatter: (p) => (p.value[2] >= 1 ? Math.round(p.value[2]) : ''), fontSize: 10, color: store.theme === 'dark' ? '#fff' : '#1e1b4b' },
				itemStyle: { borderColor: store.theme === 'dark' ? '#0b0f1a' : '#fff', borderWidth: 2, borderRadius: 4 }
			}
		]
	});

	function shares(ti) {
		const c = new Map();
		let n = 0;
		for (const m of d.members) {
			const t = m.t.find((x) => x.t === ti);
			if (!t || !m.y.length || (store.parties.length && !store.parties.includes(t.p))) continue;
			n++;
			for (const g of groupsOf(m, store.mode)) c.set(g, (c.get(g) ?? 0) + 1);
		}
		return { c, n };
	}

	const diff = $derived.by(() => {
		const A = shares(+ta);
		const B = shares(+tb);
		return d.groups
			.map((g) => {
				const a = A.n ? (100 * (A.c.get(g) ?? 0)) / A.n : 0;
				const b = B.n ? (100 * (B.c.get(g) ?? 0)) / B.n : 0;
				return { g, a, b, d: b - a };
			})
			.sort((x, y) => y.d - x.d);
	});

	const lbl = (i) => `${d.terms[i].s}–${d.terms[i].e}`;

	const diffOption = $derived({
		grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
		tooltip: {
			trigger: 'axis',
			axisPointer: { type: 'shadow' },
			formatter: (p) => {
				const r = diff[p[0].dataIndex];
				return `<b>${r.g}</b><br>${lbl(+ta)}: ${r.a.toFixed(1)} %<br>${lbl(+tb)}: ${r.b.toFixed(1)} %<br>Förändring: <b>${r.d > 0 ? '+' : ''}${r.d.toFixed(1)} p.e.</b>`;
			}
		},
		xAxis: { type: 'value', axisLabel: { formatter: '{value} p.e.' } },
		yAxis: { type: 'category', inverse: true, data: diff.map((r) => r.g), axisLabel: { width: 200, overflow: 'truncate' } },
		series: [
			{
				type: 'bar',
				data: diff.map((r) => ({ value: +r.d.toFixed(1), itemStyle: { color: r.d >= 0 ? '#34d399' : '#f87171', borderRadius: r.d >= 0 ? [0, 5, 5, 0] : [5, 0, 0, 5] } })),
				label: { show: true, position: 'right', formatter: (p) => (p.value > 0 ? '+' : '') + p.value, fontSize: 10, color: 'inherit' }
			}
		]
	});
</script>

<svelte:head><title>Jämför – Riksdagens yrken</title></svelte:head>

<h1 class="h-display mb-2 text-4xl font-bold">Jämför</h1>
<p class="mb-6 max-w-2xl text-muted">Hur skiljer sig partiernas yrkesprofil åt – och hur har riksdagen förändrats mellan två mandatperioder?</p>

<div class="mb-6"><Filters /></div>

<section class="card mb-6 p-5">
	<h2 class="text-lg font-semibold">Yrkesgrupper per parti</h2>
	<p class="mb-3 text-xs text-muted">Andel (%) av partiets ledamöter med känt yrke under {store.termLabel} som tillhör respektive yrkesgrupp.</p>
	<Chart option={heatOption} height="{Math.max(520, heat.groups.length * 30 + 90)}px" />
</section>

<section class="card p-5">
	<div class="mb-4 flex flex-wrap items-end gap-3">
		<div class="mr-auto">
			<h2 class="text-lg font-semibold">Förändring mellan två mandatperioder</h2>
			<p class="text-xs text-muted">Skillnad i andel bland ledamöter med känt yrke, procentenheter. Partifiltret ovan gäller.</p>
		</div>
		<select class="select" bind:value={ta}>{#each d.terms as t, i}<option value={i}>{lbl(i)}</option>{/each}</select>
		<span class="pb-2 text-muted">→</span>
		<select class="select" bind:value={tb}>{#each d.terms as t, i}<option value={i}>{lbl(i)}</option>{/each}</select>
	</div>
	<Chart option={diffOption} height="560px" />
</section>
