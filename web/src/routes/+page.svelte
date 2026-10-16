<script>
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { store, countGroups, groupsOf, NONE, pct } from '$lib/data.svelte.js';
	import Chart from '$lib/Chart.svelte';
	import Filters from '$lib/Filters.svelte';

	const d = $derived(store.data);
	const sel = $derived(store.selected);
	let showNone = $state(false);
	let share = $state(true);

	const counts = $derived(countGroups(sel, store.mode));
	const known = $derived(sel.filter((m) => m.y.length));
	const countsShown = $derived(counts.filter(([g]) => showNone || g !== NONE));
	const women = $derived(sel.filter((m) => m.k === 'kvinna').length);
	
	const topRaw = $derived.by(() => {
		const c = new Map();
		for (const m of sel) {
			const ys = store.mode === 'huvud' ? m.y.filter((y) => y.g === m.h).slice(0, 1) : m.y;
			for (const y of ys) c.set(y.y, (c.get(y.y) ?? 0) + 1);
		}
		return [...c.entries()].sort((a, b) => b[1] - a[1]).slice(0, 15);
	});

	const perTerm = $derived.by(() => {
		const rows = d.terms.map(() => new Map());
		const totals = d.terms.map(() => 0);
		for (const m of d.members) {
			const gs = groupsOf(m, store.mode);
			for (const t of m.t) {
				if (store.parties.length && !store.parties.includes(t.p)) continue;
				if (!showNone && gs[0] === NONE) continue;
				totals[t.t]++;
				for (const g of gs) rows[t.t].set(g, (rows[t.t].get(g) ?? 0) + 1);
			}
		}
		return { rows, totals };
	});

	const barOption = $derived({
		grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
		tooltip: {
			trigger: 'axis',
			axisPointer: { type: 'shadow' },
			formatter: (p) => `<b>${p[0].name}</b><br>${p[0].value} ledamöter (${pct(p[0].value, sel.length)})`
		},
		xAxis: { type: 'value' },
		yAxis: { type: 'category', inverse: true, data: countsShown.map(([g]) => g), axisLabel: { width: 190, overflow: 'truncate' } },
		series: [
			{
				type: 'bar',
				barWidth: '62%',
				data: countsShown.map(([g, v]) => ({ value: v, itemStyle: { color: d.groupColor[g], borderRadius: [0, 6, 6, 0] } })),
				label: { show: true, position: 'right', color: 'inherit', fontSize: 11 }
			}
		]
	});

	// Inte $state: tooltip-formattern läser värdet vid varje musrörelse,
	// och diagrammet ska inte ritas om när det ändras.
	let hoveredGroup = null;
	const areaEvents = {
		mouseover: (p) => (hoveredGroup = p.seriesName),
		mouseout: () => (hoveredGroup = null),
		globalout: () => (hoveredGroup = null)
	};

	const areaOption = $derived.by(() => {
		const groups = [...d.groups, NONE].filter((g) => showNone || g !== NONE);
		const { rows, totals } = perTerm;
		const labels = d.terms.map((t) => `${t.s}–${String(t.e).slice(2)}`);
		return {
			grid: { left: 8, right: 16, top: 16, bottom: 8, containLabel: true },
			tooltip: {
				trigger: 'axis',
				order: 'valueDesc',
				formatter: (ps) => {
					const rows = ps.filter((p) => p.value > 0).sort((a, b) => b.value - a.value);
					const shown = rows.slice(0, 12);
					const hov = rows.find((p) => p.seriesName === hoveredGroup);
					if (hov && !shown.includes(hov)) shown.push(hov);
					return (
						`<b>${ps[0].axisValue}</b><br>` +
						shown
							.map((p) => {
								const v = share ? p.value.toFixed(1) + ' %' : p.value;
								return p.seriesName === hoveredGroup
									? `<div style="font-weight:700;font-size:13px;margin:2px 0">${p.marker}${p.seriesName}: ${v}</div>`
									: `<div style="opacity:${hoveredGroup ? 0.6 : 1}">${p.marker}${p.seriesName}: <b>${v}</b></div>`;
							})
							.join('')
					);
				}
			},
			xAxis: { type: 'category', boundaryGap: false, data: labels, axisLabel: { rotate: 40, fontSize: 10 } },
			yAxis: { type: 'value', max: share && store.mode === 'huvud' ? 100 : null, axisLabel: { formatter: share ? '{value} %' : '{value}' } },
			series: groups.map((g, gi) => ({
				name: g,
				type: 'line',
				stack: 'a',
				smooth: 0.3,
				symbol: 'none',
				triggerLineEvent: true,
				lineStyle: { width: 0 },
				areaStyle: { opacity: 0.85, color: d.groupColor[g] },
				itemStyle: { color: d.groupColor[g] },
				emphasis: { focus: 'series' },
				data: rows.map((r, ti) => {
					const v = r.get(g) ?? 0;
					return share ? (totals[ti] ? (100 * v) / totals[ti] : 0) : v;
				}),
				...(gi === 0
					? {
							markArea: {
								silent: true,
								itemStyle: { color: 'rgba(167,139,250,.10)', borderColor: 'rgba(167,139,250,.6)', borderWidth: 1, borderType: 'dashed' },
								data: [[{ xAxis: labels[store.range[0]] }, { xAxis: labels[store.range[1]] }]]
							}
						}
					: {})
			}))
		};
	});

	const womenOption = $derived.by(() => {
		const rows = d.groups
			.map((g) => {
				const ms = sel.filter((m) => m.k && groupsOf(m, store.mode).includes(g));
				return [g, ms.length, ms.filter((m) => m.k === 'kvinna').length];
			})
			.filter(([, n]) => n >= 5)
			.map(([g, n, w]) => [g, (100 * w) / n, n])
			.sort((a, b) => b[1] - a[1]);
		return {
			grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
			tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `<b>${p[0].name}</b><br>${p[0].value.toFixed(1)} % kvinnor (av ${rows[p[0].dataIndex][2]})` },
			xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value} %' } },
			yAxis: { type: 'category', inverse: true, data: rows.map((r) => r[0]), axisLabel: { width: 190, overflow: 'truncate' } },
			series: [
				{
					type: 'bar',
					barWidth: '60%',
					data: rows.map((r) => ({ value: r[1], itemStyle: { borderRadius: [0, 6, 6, 0], color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#a78bfa' }, { offset: 1, color: '#f472b6' }] } } })),
					label: { show: true, position: 'right', formatter: (p) => `${Math.round(p.value)} %`, color: 'inherit', fontSize: 11 }
				}
			]
		};
	});

	function openGroup(p) {
		const g = p.name;
		goto(`${base}/yrken/?g=${encodeURIComponent(g)}`);
	}
</script>

<svelte:head><title>Riksdagens yrken – översikt</title></svelte:head>

<section class="fade-in mb-8">
	<h1 class="h-display text-4xl font-bold sm:text-5xl">
		Vad jobbade <span class="grad-text">riksdagsledamöterna</span> med?
	</h1>
	<p class="mt-3 max-w-2xl text-muted">
		Yrkesbakgrund för {d.members.length.toLocaleString('sv-SE')} personer som suttit i enkammarriksdagen under {d.terms.length} mandatperioder,
		{d.terms[0].s}–{d.terms.at(-1).e}. Dra i reglaget för att välja tidsperiod.
	</p>
</section>

<div class="mb-6"><Filters /></div>

<section class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
	{#each [
		['Ledamöter', sel.length.toLocaleString('sv-SE'), `under ${store.termLabel}`],
		['Vanligaste yrkesgrupp', counts.find(([g]) => g !== NONE)?.[0] ?? '–', `${counts.find(([g]) => g !== NONE)?.[1] ?? 0} ledamöter`],
		['Andel kvinnor', pct(women, sel.length), `${women.toLocaleString('sv-SE')} kvinnor av ${sel.length.toLocaleString('sv-SE')} ledamöter`],
		['Med känt yrke', pct(known.length, sel.length), `${sel.length - known.length} saknar uppgift`]
	] as [label, value, sub], i}
		<div class="card fade-in p-5" style:animation-delay="{i * 60}ms">
			<div class="label">{label}</div>
			<div class="mt-2 text-2xl font-bold leading-tight {i === 1 ? 'text-lg sm:text-xl' : 'tabular-nums'}">{value}</div>
			<div class="mt-1 text-xs text-muted">{sub}</div>
		</div>
	{/each}
</section>

<section class="mb-6 grid gap-6 lg:grid-cols-5">
	<div class="card p-5 lg:col-span-3">
		<div class="mb-3 flex flex-wrap items-center justify-between gap-2">
			<h2 class="text-lg font-semibold">Yrkesgrupper</h2>
			<label class="flex items-center gap-2 text-sm text-muted">
				<input type="checkbox" bind:checked={showNone} class="accent-[var(--accent)]" /> Visa "Ingen uppgift"
			</label>
		</div>
		<Chart option={barOption} height="{Math.max(320, countsShown.length * 26)}px" onclick={openGroup} />
		<p class="mt-2 text-xs text-muted">Klicka på en stapel för att se ledamöterna.</p>
	</div>
	<div class="card p-5 lg:col-span-2">
		<h2 class="mb-3 text-lg font-semibold">Vanligaste yrkestitlar</h2>
		<ol class="space-y-2">
			{#each topRaw as [y, c], i}
				<li class="flex items-center gap-3 text-sm">
					<span class="w-5 text-right text-xs text-muted tabular-nums">{i + 1}</span>
					<a href="{base}/sok/?q={encodeURIComponent(y)}" class="w-36 truncate capitalize hover:text-accent">{y}</a>
					<span class="bar-bg h-2 flex-1"><span class="block h-full rounded-full" style="width:{(100 * c) / topRaw[0][1]}%; background: linear-gradient(90deg,var(--accent),var(--accent2))"></span></span>
					<span class="w-8 text-right tabular-nums text-muted">{c}</span>
				</li>
			{/each}
		</ol>
	</div>
</section>

<section class="card mb-6 p-5">
	<div class="mb-3 flex flex-wrap items-center justify-between gap-3">
		<div>
			<h2 class="text-lg font-semibold">Yrkesgrupper över tid</h2>
			<p class="text-xs text-muted">Per mandatperiod. Markerat område = valt tidsintervall.</p>
		</div>
		<div class="seg">
			<button class:on={share} onclick={() => (share = true)}>Andel</button>
			<button class:on={!share} onclick={() => (share = false)}>Antal</button>
		</div>
	</div>
	<Chart option={areaOption} height="460px" events={areaEvents} />
</section>

<section class="card p-5">
	<h2 class="text-lg font-semibold">Andel kvinnor per yrkesgrupp</h2>
	<p class="mb-3 text-xs text-muted">Yrkesgrupper med minst 5 ledamöter.</p>
	<Chart option={womenOption} height="440px" />
</section>
