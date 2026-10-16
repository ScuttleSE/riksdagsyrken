<script>
	import { onMount } from 'svelte';
	import { store } from './data.svelte.js';

	let { option, height = '360px', onclick = null } = $props();
	let el;
	let chart = $state(null);
	let echarts;

	onMount(() => {
		let ro;
		let disposed = false;
		import('echarts').then((mod) => {
			if (disposed) return;
			echarts = mod;
			chart = echarts.init(el, null, { renderer: 'canvas' });
			if (onclick) chart.on('click', onclick);
			ro = new ResizeObserver(() => chart?.resize());
			ro.observe(el);
		});
		return () => {
			disposed = true;
			ro?.disconnect();
			chart?.dispose();
		};
	});

	$effect(() => {
		if (!chart) return;
		const dark = store.theme === 'dark';
		const text = dark ? '#cbd5e1' : '#334155';
		const grid = dark ? 'rgba(148,163,184,.12)' : 'rgba(100,116,139,.15)';
		chart.setOption(
			{
				backgroundColor: 'transparent',
				textStyle: { fontFamily: 'Inter, system-ui, sans-serif', color: text },
				tooltip: {
					backgroundColor: dark ? 'rgba(15,23,42,.95)' : 'rgba(255,255,255,.97)',
					borderColor: dark ? '#334155' : '#e2e8f0',
					textStyle: { color: dark ? '#e2e8f0' : '#0f172a' },
					...(option.tooltip ?? {})
				},
				...option,
				xAxis: axis(option.xAxis, text, grid),
				yAxis: axis(option.yAxis, text, grid),
				legend: option.legend ? { textStyle: { color: text }, ...option.legend } : undefined
			},
			true
		);
	});

	function axis(a, text, grid) {
		if (!a) return undefined;
		const fix = (x) => ({
			...x,
			axisLabel: { color: text, ...(x.axisLabel ?? {}) },
			axisLine: { lineStyle: { color: grid } },
			splitLine: { lineStyle: { color: grid } }
		});
		return Array.isArray(a) ? a.map(fix) : fix(a);
	}
</script>

<div bind:this={el} style:height class="w-full"></div>
