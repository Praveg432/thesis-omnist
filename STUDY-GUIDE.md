# Study Guide: Concepts Behind the Thesis

*Uncertainty Quantification for Spatiotemporal Forecasting at Unseen Sensor Locations in Evolving Networks*

This guide is for the candidate and for anyone new to the field: a reviewer, an examiner, a lab-mate. It explains
every concept the thesis relies on, from basic forecasting to the specific evaluation choices, and ends with the
questions an examiner is likely to ask, with answers grounded in the results. Numbers quoted here come from
`SEM3-PROGRESS-REPORT.md`, where each one is tied to a result file.

**How to use it.** Parts 1 to 6 are background, in the order you need them. Part 7 is the thesis itself, told as a
story. Part 8 is the Phase 2 plan. Part 9 is the question bank. Part 10 is a glossary. If you have one hour, read
Part 1, Part 5 (conformal prediction), Part 7 and Part 9.

---

## Contents

1. The problem in one page
2. Forecasting basics
3. Spatiotemporal data and sensor networks
4. Neural network building blocks used here
5. Uncertainty and conformal prediction
6. Evaluation methodology and research hygiene
7. The thesis so far: Phase 1 as a story
8. Phase 2: the lifecycle plan
9. Question bank with answers
10. Glossary
11. Reading list, in order

---

## 1. The problem in one page

A city runs a network of sensors: air-quality monitors, road speed detectors, weather stations. It wants forecasts
(what will PM2.5 be tomorrow at this site?) and acts on them (issue an alert, reroute traffic).

Two facts about real networks make this hard.

1. **The network changes.** Sensors break, go offline and get installed at new sites. A forecaster trained on a
   fixed list of sensors cannot produce anything for a sensor it never saw. We want a model that forecasts at a new
   location **without retraining**. This is called **inductive** forecasting.
2. **A single number is not enough.** "PM2.5 will be 180" is not actionable unless you know how wrong it might be.
   We want a **prediction interval**, for example [140, 230], that contains the true value with a stated
   probability, such as 90%. The fraction of times the interval contains the truth is called **coverage**.

The thesis asks: **can we give intervals with correct coverage at sensors the model never saw, using only
information available at the time of the forecast, and where does that fail?**

The main tool is **conformal prediction**: a way to turn any forecaster's errors on held-out data into intervals with
a coverage guarantee, under an assumption called exchangeability. Much of the thesis is about when that assumption
holds for sensor networks and what to do when it does not.

Three phrases to keep straight from the start:

| Phrase | Meaning |
|---|---|
| Unseen sensor | A station whose data was never used to train the model |
| Forecast-time information | Only data that would really exist at the moment the forecast is issued; no future errors |
| Marginal coverage | Coverage averaged over stations and time, not guaranteed for each station |

---

## 2. Forecasting basics

### 2.1 Vocabulary

- **Time series.** A sequence of measurements at regular steps: hourly PM2.5, 5-minute road speed.
- **Input window (lookback).** The past values the model reads, for example the last 48 steps.
- **Horizon.** How far ahead the model predicts; a forecast can cover several future steps at once.
- **Forecast origin.** The time at which the forecast is issued. Everything after the origin is unknown.
- **Stride.** How far apart consecutive training windows start. Stride equal to the window length gives
  non-overlapping windows; a smaller stride gives overlapping windows and more training examples. (This mattered on
  PeMS-BAY; see Part 7.7.)
- **Seasonality / period.** A repeating pattern: traffic has a daily cycle (288 steps at 5 minutes, 48 at 30
  minutes); air quality has weekly and yearly cycles.

### 2.2 Baselines every forecaster must beat

A learned model is only interesting if it beats simple rules. Examiners always ask about these.

| Baseline | Rule | Why it is strong |
|---|---|---|
| **Persistence** (naive) | Tomorrow = today (last observed value) | Very hard to beat at short horizons for slowly varying signals |
| **Seasonal-naive** | Value at the same time one period ago (yesterday same hour, last week same day) | Very strong for strongly periodic signals like traffic |
| **Interpolators** | At an unseen site, average neighbours: nearest neighbour, inverse-distance weighting (IDW), k-neighbour mean, Gaussian process (kriging) | The obvious way to fill a spatial gap |

In this thesis: OmniST beats persistence on Delhi, Beijing and PeMS-BAY, ties on weather, and loses on PeMSD7-M
(error 3.79 against 3.63). On PeMS-BAY, seasonal-naive has lower error (3.47 against 4.73) and 33% narrower
intervals. Say this plainly when asked.

### 2.3 Error metrics

- **MAE (mean absolute error)** = average of |y − ŷ|. In the data's units (µg/m³, mph, °C). Robust to outliers.
- **RMSE** = square root of mean squared error. Penalises large errors more.
- **Relative change** ("16.2% lower error") = 1 − (model MAE / baseline MAE).

### 2.4 Normalisation and leakage

Inputs are usually standardised (subtract a mean, divide by a standard deviation). The statistics must come from
the **training data only**; computing them on the whole series leaks information from the test period. The same
applies to filling missing values: the report notes that missing-value filling used the full series, and measured
that the affected fraction on Delhi is 0.0074% of test entries (negligible).

**Leakage** means any path by which information from the evaluation data reaches the model or the calibration. It
is the most common reason published results do not reproduce. Two kinds matter here: temporal leakage (using the
future) and spatial leakage (a "held-out" station whose data was used in training).

### 2.5 Chronological splits

Time series must be split by time: train on earlier periods, test on later ones. Random splitting of time steps
leaks the future. In this thesis there are **two** splits at once: stations are split at random (train,
calibration, test), and time is split chronologically (training years before the test year).

---

## 3. Spatiotemporal data and sensor networks

### 3.1 What makes data spatiotemporal

Each value has a location and a time. Nearby sensors are correlated (spatial dependence), and each sensor's values
are correlated over time (temporal dependence). Both dependencies break the "independent samples" assumption of
textbook statistics, which matters for the coverage guarantee (Part 5.6).

### 3.2 Graph view of a network

A sensor network is often treated as a graph: sensors are nodes, edges connect sensors that influence each other
(by road connectivity or distance). An **adjacency matrix** A (N × N) stores edge weights. Graph neural networks
(GNNs) pass information along edges.

### 3.3 Transductive versus inductive

| | Transductive | Inductive |
|---|---|---|
| Sensors at test time | The same set as in training | May include sensors never seen |
| Typical models | STGCN, DCRNN (fixed adjacency, per-node parameters) | IGNNK, KITS, MoGERNN, OmniST |
| New sensor | Requires retraining or fails | Forecast directly from neighbours and shared parameters |

A model is inductive if its parameters do not depend on node identity. OmniST achieves this with shared weights,
coordinates instead of node IDs, and neighbours found from coordinates at each forward pass.

### 3.4 Kriging, cold start, and the sensor lifecycle

- **Kriging** (from geostatistics, named after D. G. Krige): estimate the value at an unobserved location from
  observed neighbours. **Spatiotemporal kriging** does it for every time step. **Inductive kriging** does it for
  locations not seen in training.
- **Cold start (Day 0).** A newly installed sensor has no history. The model must forecast from neighbours only.
- **Warm-up.** As the sensor accumulates data, its own history becomes usable, both as model input and for
  calibration.
- **Lifecycle.** Day 0 → warm-up → full history. Phase 2 studies forecasting and calibration across this whole path.

### 3.5 The five datasets

| Dataset | Domain | Stations | Step | Notes |
|---|---|:---:|---|---|
| Delhi PM2.5 | Air quality | 37 (21 / 8 / 8 per split) | Per-day scores | Strong seasonality; winter peaks; error roughly doubles through the test year |
| Beijing PM2.5 | Air quality | 12 (6 / 3 / 3) | Per-day scores | Few stations, so each split tests only 3 |
| NOAA GHCN weather | Weather | 30 (18 / 6 / 6) | Daily | Sparse network, about 81 km spacing |
| PeMSD7-M | Road speed, Los Angeles district 7 | 228 (168 / 30 / 30) | 5 minutes | Coordinates reconstructed from the distance matrix |
| PeMS-BAY | Road speed, San Francisco Bay Area | 325 (235 / 45 / 45) | 30 minutes in the thesis loader | Coordinates reconstructed; series covers months, not years |

Phase 2 also names **LargeST** (a California benchmark with about 8,600 sensors) for compute scaling, and a larger
**GHCN** subset (300 to 1,500 stations) for the distance test.

Know why the traffic coordinates are "reconstructed": the public datasets give a road-distance matrix, not latitude
and longitude, so positions were embedded into a plane that approximately preserves those distances. Distances in
that plane are not comparable with geographic distances in the other datasets.

### 3.6 Network spacing

To compare distances across networks, the thesis measures distance in units of **spacing**: the median distance
from each station to its nearest other station. "Two spacings away" means twice the typical gap between neighbours.

---

## 4. Neural network building blocks used here

### 4.1 Recurrent networks and the GRU

A **recurrent neural network (RNN)** reads a sequence one step at a time and keeps a hidden state that summarises
the past. The **GRU (gated recurrent unit)** adds gates that decide how much of the old state to keep and how much
to overwrite, which makes training on long sequences stable. A **bidirectional** GRU reads the input window forwards
and backwards and concatenates both summaries; this is allowed because the whole input window is in the past.

**Shared GRU (coordinate-free GRU).** One GRU with the same weights applied to every sensor separately, with no
coordinates and no attention. It is inductive (works at any sensor) but uses no spatial information. It is the key
control in this thesis: OmniST's accuracy is within about ±2% of it on all five networks.

### 4.2 Attention

Attention lets each element of a set compute a weighted average of the others, where weights depend on learned
similarity:

```
Attn(i) = Σ_j  softmax_j( q_i · k_j / √d ) · v_j
```

- q (query), k (key), v (value) are learned linear projections of each element's representation; d is their size.
- The softmax makes the weights positive and sum to 1.
- **Full (dense) attention** over N sensors compares every pair: time and memory grow as **N²**.
- **k-nearest-neighbour attention** restricts each sensor to its k nearest neighbours: cost grows as **N × k**.
  In Phase 2 this cut attention memory 2.6 times at N = 2,000 and 16.7 times at N = 8,000, with no advantage below
  about 1,000 sensors, and output equal to exact attention (cosine similarity at least 0.99987).
- **Distance-biased attention** adds a learned function of the relative position e_ij (Δlat, Δlon, distance,
  log(1 + distance)) to the logits: softmax(q·k/√d + ψ(e_ij)). It uses only relative geometry, so it is
  translation-invariant.

### 4.3 Coordinate embeddings and why they generalise poorly

OmniST v1 embeds each sensor's absolute coordinates (lat, lon) through a learned function. At an unseen location,
the absolute coordinate is a new input value, so the model must interpolate a learned spatial field. Relative
geometry (distance and direction to neighbours) transfers better because the same patterns recur everywhere. This is
part of why the Phase 2 upgrades use relative features.

The **coordinate-normalisation defect** (Part 7.6) is a concrete lesson: the embedding centred and scaled inputs
with constants fixed for Delhi, so on other networks the inputs were 132 to 656 times outside the intended range.

### 4.4 Residual connections and gates

- **Residual connection:** output = input + f(input). The layer learns a correction, which is easy to make small.
- **Zero-initialised gate:** output = h + γ · f(h), with γ starting at 0. The model starts as the simpler model
  (here, the shared GRU) and only uses the extra branch if training finds it helpful. This is a way to guarantee
  "no worse than the baseline at initialisation", not at convergence.

### 4.5 Seasonal-residual and scale head

Instead of predicting the value y directly, predict the **residual from the seasonal value**: ŷ = y_{t−P} + f(·),
where P is the period. The network then spends its capacity on deviations from the usual daily pattern, not on
re-learning the pattern. A second output, a **scale** σ̂ > 0, estimates how uncertain this forecast is. Training
minimises

```
loss = |y − ŷ| / σ̂  +  log σ̂
```

which is the negative log-likelihood of a Laplace distribution: errors are penalised less where the model admits
high uncertainty, and the log term stops it from admitting uncertainty everywhere. The conformal score is then the
**normalised** error |y − ŷ| / σ̂ (Part 5.5), giving intervals that are wide where σ̂ is large and narrow elsewhere.

### 4.6 Masked-station training

During training, hide the input history of a random fraction (here 20%) of training stations and still ask the
model to forecast them, using only their neighbours. This forces the spatial branch to learn to transfer
information between stations, because the station's own history is not available. Without masking, every training
station always sees its own history, the temporal branch solves the task alone, and the spatial branch stays idle
(a form of **shortcut learning**). KITS (AAAI 2025) uses a related idea with virtual nodes.

### 4.7 State-space models (Mamba)

Selective state-space models process sequences in time linear in their length and can be parallelised on GPUs with
special kernels. The thesis tried one as the temporal block. On the Apple M4 Pro it was about 2.0 to 2.2 times slower
than the GRU (no fused kernel on this hardware), and the full model with it failed the pre-registered parity gate
(error worse by 6.4 against a margin of 2.4). It was dropped. Know this if asked "why not Mamba?".

### 4.8 Inference memory and the M4 Pro

All work runs on one Apple M4 Pro laptop (Apple's MPS GPU backend, about 24 GB unified memory). This constrains
model size, network size and the number of repeated runs, and is why compute claims are measured as peak memory and
time on this machine, not as GPU-cluster throughput.

---

## 5. Uncertainty and conformal prediction

This is the core of the thesis. Be able to derive the split conformal guarantee on a whiteboard.

### 5.1 Kinds of uncertainty

- **Aleatoric:** irreducible noise in the data (weather is chaotic).
- **Epistemic:** the model's ignorance, larger at unfamiliar inputs (an unseen sensor in an unusual place).
- Conformal prediction does not separate them; it calibrates total predictive error.

### 5.2 Prediction interval versus confidence interval

- A **confidence interval** covers an unknown *parameter* (for example, the mean coverage over splits:
  0.893 [0.884, 0.901]).
- A **prediction interval** covers a future *observation* (tomorrow's PM2.5).
- The thesis uses both: prediction intervals are the product; confidence intervals summarise how the coverage of
  those prediction intervals varies over random station splits.

### 5.3 Judging intervals: coverage, width, interval score

- **Coverage:** fraction of true values inside the interval. Target here: 0.90 (miscoverage level α = 0.10).
- **Width:** u − l. A trivially wide interval has perfect coverage and no use. Good intervals have the target
  coverage and small width.
- **Interval (Winkler) score** for an interval [l, u] at level α:

```
S = (u − l)  +  (2/α)·(l − y)  if y < l
             +  (2/α)·(y − u)  if y > u
```

  At α = 0.10 a miss costs 20 times its distance. Lower is better. It rewards narrow intervals but punishes misses,
  so it is the single number used to compare methods' usefulness (C1h, C1i, D).
- **Marginal coverage:** averaged over all test points. **Conditional coverage:** for each station, or each
  condition. Conformal methods guarantee marginal coverage; conditional coverage is generally impossible to
  guarantee without assumptions. Per-station coverage in C1 ranged down to 0.40 on PeMS-BAY even when the mean was
  0.892. This is why per-station coverage (contribution A) is its own goal.

### 5.4 Split conformal prediction: the recipe

1. Train a forecaster on the training set.
2. On a separate **calibration set** of n examples, compute a **nonconformity score** for each, for example
   s_i = |y_i − ŷ_i|.
3. Let q̂ be the ⌈(n + 1)(1 − α)⌉-th smallest score.
4. For a new point, output the interval [ŷ − q̂, ŷ + q̂].

**Guarantee.** If the calibration scores and the test score are **exchangeable**, then

```
P( Y_new ∈ [ŷ − q̂, ŷ + q̂] )  ≥  1 − α
```

and if scores have no ties, coverage is also at most 1 − α + 1/(n + 1). The proof is a ranking argument: under
exchangeability the test score is equally likely to fall in any of the n + 1 rank positions, so the probability that
it exceeds the ⌈(n + 1)(1 − α)⌉-th calibration score is at most α. No assumption is made about the model or the data
distribution; the guarantee holds for finite n.

Things to say precisely:
- The guarantee is **marginal**, over the random draw of calibration and test data.
- It is about **this** calibration rule and **this** test distribution; if the test data differ systematically from
  the calibration data, the guarantee fails.
- The model can be arbitrarily bad; a bad model gives wide intervals, not wrong coverage.

### 5.5 Normalised (locally adaptive) scores

With s = |y − ŷ| / σ̂(x), the interval becomes [ŷ − q̂·σ̂(x), ŷ + q̂·σ̂(x)]: wider where σ̂ is larger. The guarantee
still holds (it is just a different score), but width now adapts to local difficulty. The thesis uses two scalings:
- **Forecast magnitude:** σ̂ = mean |forecast| over the horizon (the "scaled by forecast magnitude" rule, C1e to C1i).
  It works because air-quality error grows with the pollution level.
- **Learned scale:** σ̂ from the scale head (Part 4.5; Phase 2 D).

### 5.6 Exchangeability, and why the station is the unit

**Exchangeable** means the joint distribution does not change if you reorder the items. i.i.d. data are
exchangeable; exchangeability is weaker.

In a sensor network, scores at the same station on different days are strongly dependent, and nearby stations are
correlated. So individual scores are not exchangeable. What is approximately exchangeable, when stations are split
at random, is **whole stations**: a randomly chosen test station is like a randomly chosen calibration station.

Consequences to understand:
- Pooling all scores from 8 calibration stations into one quantile treats thousands of dependent scores as if they
  were independent. The effective calibration size is closer to the **number of stations** (3 to 45 here) than to
  the number of scores.
- Therefore the coverage statement is **approximate**, and the thesis checks it **empirically** over many random
  splits instead of relying on the theorem.
- **Hierarchical (station-level) conformal prediction** makes the station the unit explicitly: each calibration
  station gets equal weight, and the guarantee is over stations. With 10 calibration stations at 90%, the theory
  allows coverage up to 0.90 + 2/11, so it is conservative with few stations; its width cost fell from 90% (10
  stations, Delhi) to 31% (30 stations, PeMSD7-M). It needs at least 9 calibration stations at a 90% target, because
  ⌈(n + 1) × 0.9⌉ must not exceed n.

### 5.7 Temporal shift and forecast-time calibration

The central Phase 1 finding is about **time**, not space.

- **Same-window calibration (C1's rule):** the quantile for a test window uses calibration-station errors over the
  same test period, including windows *after* it. This information does not exist when the forecast is issued.
- **Chronological (forecast-time) calibration (C1b):** the quantile for window t uses only calibration errors from
  windows before t.
- If error grows over the test period (Delhi: late-third error is 1.90 times early-third), chronological
  calibration lags behind and under-covers: 0.811 on Delhi, 0.778 on Beijing.
- Same-window calibration hides this because it already "knows" the later, larger errors.

This is a form of **distribution shift over time** (non-stationarity). Tools to know:

| Tool | Idea | Used here |
|---|---|---|
| Expanding window | Quantile over all earlier errors | Default chronological rule; enough for traffic |
| Rolling window | Quantile over the most recent errors only | Tried in C1e; partial recovery |
| Multi-year, same-season | Quantile over earlier *years'* errors from the same season (within 45 days) | The confirmed rule for air quality and weather |
| Scaled scores | Divide errors by forecast magnitude so the quantile is comparable as levels change | Combined with the multi-year rule |
| Adaptive conformal inference (ACI) | Adjust α online: raise it after a miss, lower it after a hit, so long-run coverage tracks the target | Original-protocol drift experiment; Phase 2 B |
| Weighted conformal | Weight calibration scores by how similar they are to the test point (covariate shift, beyond exchangeability) | Related work; candidate for C |
| Online rule selection | At each origin pick the rule with the best past interval score | C1i: works on weather and Delhi, fails on Beijing (0.868) |

### 5.8 Other conformal variants named in the thesis

- **Localised conformal** (Hore and Barber; Mao, Martin and Reich): weight calibration points by proximity to get
  closer to local coverage. Candidate geometry-aware methods for C.
- **Cluster-aware calibration:** calibrate separately per cluster of similar stations.
- **Spatial whitening:** transform spatially dependent scores to be closer to exchangeable.
- **Conformal risk control:** generalises coverage to control the expected value of any bounded loss, for example
  the miss rate of threshold alerts (contribution F).
- **Mondrian conformal:** separate quantiles per category (for example, per hour of day: the time-of-day rule in
  C1i is in this spirit).

---

## 6. Evaluation methodology and research hygiene

Examiners at strong institutes probe method more than results. These are the choices to defend.

### 6.1 Random disjoint station splits, many times

Each split assigns stations at random to train, calibration and test; the model never sees calibration or test
stations. Results are averaged over many splits (20 for the small datasets, 6 then 20 for traffic). The **split is
the unit of inference**: the reported 95% interval is over splits.

Why not one fixed held-out set with several seeds? Because seed-to-seed spread on fixed stations measures
initialisation noise, not variation across which stations happen to be new. The original protocol (fixed 3 to 7
stations) gave 1 to 2.5 points higher coverage than random splits.

### 6.2 Region holdout (C2)

To test whether distance from the network matters, hold out a contiguous region (a random station and its nearest
neighbours) instead of scattered stations, draw calibration stations from outside the region, and regress coverage
on distance **within station** (the same station appears at different distances in different splits), which removes
the effect of some stations simply being noisier.

### 6.3 Paired comparisons and confidence intervals

When comparing method A with B, compute the difference on each split and form an interval for the mean difference
(a **paired** comparison). This removes split-to-split variation common to both. "−0.91 [−1.04, −0.78]" means A's
error is lower by 0.91 on average, with a 95% interval that excludes zero. An interval that includes zero means the
difference is not established, not that it is zero.

### 6.4 Pre-registration

Before running a confirmation experiment, commit to git the hypotheses, the exact rule, the data (fresh splits) and
the pass criteria. The commit timestamp proves the order. This prevents the **garden of forking paths**: trying many
variants and reporting the one that worked. The thesis has four pre-registered rounds: C1h, C1i/C1j, and two
feasibility rounds for Phase 2. Results chosen after seeing data (C1f) are labelled exploratory and then confirmed.

### 6.5 Fresh data for confirmation

A rule chosen on splits 0 to 19 is confirmed on splits 20 to 39 and on a network not used to choose it (weather in
C1h). Reusing selection data for confirmation overstates performance.

### 6.6 Controls and ablations

- **Negative control:** a setting where you expect no effect; finding one there signals a bug. Delhi is the negative
  control for the Day-0 claim in Phase 2.
- **Backbone control:** replace the architecture with a simpler one (the shared GRU). If results hold, the
  contribution is the calibration, not the model.
- **Ablation:** remove one component at a time (distance bias, attention, mask) to find where a gain comes from.
- **Exact-reproduction control:** before testing a change in the thesis pipeline, check that the unchanged pipeline
  reproduces the stored result exactly (done for the time-of-day test).

### 6.7 Equivalence (parity) tests

To claim two models are "the same" (k-NN attention versus exact attention), fix a margin in advance and show the
confidence interval of the difference lies inside it. Failing to find a difference is not evidence of equivalence.
V1b did this: GO for k-NN attention (difference 0.0001 inside a 2.43 margin), NO-GO for the state-space block.

### 6.8 Reporting negatives

Criteria are fixed in advance, and every contribution has a fallback, so a negative answer is a result: for
example, "distance did not matter once the defect was fixed". Examiners respect this if it is stated plainly.

### 6.9 Verification tooling in the repository

Every number in the report is checked against committed result files by scripts in `tools/` (for example
`tools/check_c1b_report.py`, 158 figures). The verification steps are logged in `FINALIZATION-RECORD.md`. If asked
"how do you know the report matches the code?", this is the answer.

---

## 7. The thesis so far: Phase 1 as a story

### 7.1 OmniST in three design choices

1. **Coordinate tokenisation:** each sensor is represented from its coordinates, not an index, so there is no fixed
   node count.
2. **k-NN spatial attention:** neighbours are found from coordinates at every forward pass; no stored adjacency.
3. **Per-sensor temporal processing:** a bidirectional GRU per sensor with shared weights.

Plus split conformal intervals calibrated on held-out stations. A locality check: changing a far-away sensor changed
a prediction by 8.9 × 10⁻⁸, so a sensor's score depends only on its neighbourhood. That is an invariance property,
not a proof of exchangeability.

Preprint: arXiv:2611.04256.

### 7.2 Step 1: the random-split re-evaluation (C1)

A preliminary review found two problems with the first protocol (fixed held-out stations; calibration on training
stations). C1 re-ran everything with random disjoint splits and calibration on separate stations.
Result: mean coverage 0.876 to 0.906 across five networks, every interval containing 0.90. But per-station minimums
went as low as 0.40, and only a third to a half of splits reached 0.90.

### 7.3 Step 2: the forecast-time problem (C1b, C1d, C1c)

C1's calibration used same-period errors. With forecast-time (chronological) calibration, coverage fell to 0.811
(Delhi) and 0.778 (Beijing); weather and traffic stayed near target (0.881 to 0.891, corrected frame). The forecast-time range
is 77.8% to 89.1%. Diagnosis: on the air-quality networks, error roughly doubles through the test year (ratios 1.90
and 2.11), while calibration and test stations have similar error (ratios about 1.0). So the cause is **change over
time**, not station mismatch. Persistence and seasonal-naive under-cover in the same two networks, so the problem
belongs to the data and the calibration rule, not to OmniST.

### 7.4 Step 3: repairing it, then confirming (C1e to C1j)

- Using **earlier years' errors from the same season, scaled by forecast magnitude** brought Delhi and Beijing close
  to 0.90 (exploratory C1f).
- **Pre-registered C1h** on fresh splits and an unused network: 0.902 (Delhi), 0.890 (Beijing), 0.908 (weather).
  OmniST's intervals then beat persistence and seasonal-naive on interval score on all three. On weather the rule
  widened intervals without need (H4 failed).
- **Pre-registered C1i** with four times more forecast origins: 0.908, 0.900, 0.913. On traffic the seasonal rule is
  unnecessary; plain expanding calibration gives 0.891 and 0.881 (0.896 and 0.883 over 20 splits).
- **Station-level conformal** repairs per-station coverage at a width cost: on PeMS-BAY 0.906 with stations below
  0.80 cut from 13.9% to 6.2%, about 25% wider.

**Summary sentence to memorise:** every network now has a forecast-time calibration method confirmed within 0.02 of
the 90% target on data not used to design it; the cost is width (about 25% to 60%).

### 7.5 Step 4: does distance matter? (C2, C3)

With the original code, coverage in the sparse weather network fell 1.4 points per extra spacing. After the
coordinate defect was fixed, the slope was −0.2 points per spacing with an interval including zero: the effect did
not reproduce. C3 showed that a total-variation-based coverage bound would be vacuous at these sample sizes (noise
floor about 0.13 exceeds the 0.10 miscoverage budget), so that line was dropped.

### 7.6 Defects found and how they were handled

| Defect | Effect | Fix |
|---|---|---|
| Coordinate constants fixed for Delhi | Inputs 132 to 656 times out of range elsewhere; error and width inflated (PeMSD7-M MAE 10.33 → 3.79) | Frame built from training stations; both versions reported |
| Neighbour cache key collision | Two layouts could share a cache entry | Hash of exact coordinates, tests |
| First parity check could not fail | V1 gave no evidence | V1b with margins and disjoint calibration |
| Scale-up result calibrated each window on its own errors | Not forecast-time | Re-run deployable; 0.880 at 4,000 synthetic sensors |
| Timestamp unit in the first traffic C1i run | Some infinite intervals | Fixed; script refuses infinite intervals |
| Training stride on traffic (open) | PeMS-BAY training windows all start at one clock phase; exploratory 19% error drop | Flagged in the report; pre-registered test S0 first in Phase 2 |

Being able to explain these calmly is a strength: it shows the checks work.

### 7.7 The backbone control and what it means

A shared GRU with no coordinates and no attention matches OmniST's error within about ±2% on all five networks. So
the ability to forecast at unseen sensors comes from **parameter sharing**, and the thesis contribution is **the
calibration and its evaluation, not the architecture**. This is the most likely hostile question; Part 9 has the
answer.

---

## 8. Phase 2: the lifecycle plan

### 8.1 Framing

"Calibrated forecasting across a sensor's lifecycle, from Day 0 to warm, using only forecast-time information."
Day-0 forecasting is published (IGNNK 2021, KITS 2025, MoGERNN 2025). What is claimed as new is valid intervals
across the transition from no history to full history.

### 8.2 What the feasibility rounds showed (pre-registered, 26 Nov 2026)

| Finding | Number |
|---|---|
| Masked training gives a better Day-0 forecaster than interpolating a shared GRU's neighbour forecasts | 16.2% lower error on PeMS-BAY, 10.3% on PeMSD7-M (10 splits each); not on Delhi (1.2%, not significant) |
| Where the gain comes from | A plain neighbour mean keeps 14.7% and 9.9%; distance-biased attention adds about 2% on PeMS-BAY only |
| Day-0 intervals | Coverage 0.879 and 0.880; interval score better than the baseline |
| Sensors with history | The spatial branch does not beat the shared GRU; masked training costs −2.0% to +1.3% |
| Seasonal-residual + scale head | PeMS-BAY interval score 25.9 against 40.9 for seasonal-naive (37% lower); a plain GRU with the same head scores 26.1 |
| Time of day as an input | Changes error by 0.1% and 0.7%: refuted |
| Training stride (exploratory) | Overlapping windows: PeMS-BAY error 4.62 → 3.73 on 3 splits |

### 8.3 The steps

| Step | Question | Pass rule (summary) |
|---|---|---|
| S0 | Does the stride fix hold on all 6 splits? | Lower PeMS-BAY error, interval below 0, coverage within 0.02 |
| B (headline) | How do error, coverage and width change from Day 0 to full history? | Day-0 error at least 5% below baseline; full-history error at most 1.01 × shared GRU; coverage within 0.03 everywhere; width at 60 days at least 5% below Day 0 |
| D | Are traffic intervals useful? | Interval score below seasonal-naive and persistence on both road networks |
| A | Per-station coverage | At most 5% of stations below 0.80; width at most 30% above the pooled rule |
| C (gated) | Does position matter on a large sparse network? | Gate: far tercile at least 0.03 below near |
| E | Scale and comparisons | Memory, coverage against N; results repeated with the shared GRU |
| F, G | Alerts; package and thesis | Miss rate; reproducible table |

Two concepts you need for B:
- **Two history axes.** *Model-input history* (how much of the input window the sensor has filled: hours on traffic,
  days on Delhi) and *calibration history* (how many days of the sensor's own errors exist for conformal). They grow
  at different rates.
- **Partial-history masking.** All-or-nothing masking trains Day 0 only. To train a smooth warm-up, mask a random
  prefix of each training station's window, from none to full.

Full plan: `THESIS-COMPLETION-PLAN.md`.

---

## 9. Question bank with answers

Answers are short on purpose. Expand only if asked.

### About the problem and contribution

**Q1. What exactly is new in this thesis?**
An evaluation protocol for coverage at unseen sensors that uses only forecast-time information; the finding that
the common same-period protocol overstates coverage (by up to 12.5 points on Beijing); calibration rules matched to
network type, confirmed in pre-registered tests on fresh data; and, in Phase 2, calibrated intervals across a new
sensor's lifecycle. The architecture is not the contribution.

**Q2. A shared GRU matches OmniST. Why should anyone care about OmniST?**
They should not care about OmniST's accuracy, and the thesis says so. The finding is itself useful: inductive
ability comes from parameter sharing, not coordinates or attention, on these networks. Every calibration result is
being repeated with the shared GRU as backbone, so the contribution does not depend on OmniST. The architecture's
remaining role is memory at large N and the Day-0 spatial branch, which the GRU alone cannot provide.

**Q3. Isn't Day-0 forecasting already solved by IGNNK, KITS, MoGERNN?**
Day-0 point forecasting is published, and the thesis cites it. None of those reports forecast-time intervals or
coverage across the transition from Day 0 to a full history. That transition is the claim.

**Q4. Why 90%?**
Standard in the conformal literature and operationally meaningful; the methods work for any level. Hierarchical
conformal needs at least 9 calibration stations at 90%, which several networks satisfy.

### About conformal prediction

**Q5. State the split conformal guarantee and its assumption.**
If calibration and test scores are exchangeable, P(test value in interval) ≥ 1 − α, at most 1 − α + 1/(n + 1)
without ties. The assumption is exchangeability; nothing about the model.

**Q6. Your scores are dependent over time and space. Is the guarantee valid?**
Not as a theorem at the level of individual scores. Exchangeability is plausible at the level of stations because
stations are split at random. The pooled quantile is therefore approximate, with an effective sample size near the
number of calibration stations. The thesis checks coverage empirically over many random splits, and uses
station-level conformal where per-station validity matters.

**Q7. Why did C1 look fine but forecast-time coverage fail?**
C1 calibrated on errors from the same period it evaluated, including later windows. Forecast-time calibration only
has earlier errors. When error grows through the year (air quality, ratio about 2), earlier errors understate later
ones, and coverage falls to 0.78 to 0.81.

**Q8. Is the forecast-time shortfall OmniST's fault?**
No. Persistence and seasonal-naive under-cover in the same two networks under the same rule. It is a property of the
data's non-stationarity and the calibration rule.

**Q9. Why does the scaled, same-season, multi-year rule work?**
Same season handles the yearly cycle (winter errors calibrate winter forecasts). Scaling by forecast magnitude makes
errors comparable across pollution levels. Earlier years give enough history, which a single test year lacks.

**Q10. What does station-level conformal cost and why?**
Width, 25% to 90% depending on the number of calibration stations. With few stations the quantile must be taken at a
high rank of a small set, which is conservative (coverage up to 0.90 + 2/11 with 10 stations). The cost falls as
stations increase.

**Q11. Why not just use quantile regression or a Bayesian model?**
They give intervals whose coverage depends on the model being right. Conformal adds a finite-sample, model-free
guarantee under exchangeability, and can wrap a quantile or scale head (Phase 2 D does exactly that).

**Q12. What is the interval score and why use it?**
Width plus 2/α times the size of any miss. It combines coverage and width into one proper score, so a method cannot
win by being too wide or too narrow.

### About evaluation

**Q13. Why random station splits rather than one held-out set?**
The question is about *any* new sensor, so the randomness that matters is which stations are new. Seeds on fixed
stations measure initialisation noise. The fixed set gave coverage 1 to 2.5 points higher.

**Q14. Only 6 traffic splits. Enough?**
They were extended to 20 (not pre-registered, same code); results agree, and the PeMS-BAY interval then excludes
0.90, showing a small real under-coverage that station-level conformal removes.

**Q15. How do I know you didn't tune until something passed?**
Four pre-registered rounds with committed rules, fresh splits, and an unused network; failures are reported (C1h H4,
C1i H7, feasibility F1, L2). Commit timestamps show order.

**Q16. Are the baselines fair?**
Persistence, seasonal-naive and interpolators are exact. E-STGCN and IGNNK are the author's re-implementations, so
equal tuning is not verified; official IGNNK code is planned in E. The main comparisons that matter now are against
persistence, seasonal-naive and the shared GRU, which are not tuning-sensitive.

**Q17. Beijing has 12 stations and 3 test stations per split. What can you claim?**
Mean coverage over 20 splits, with intervals. Per-split statements are weak, and the report says so. Hierarchical
conformal cannot run with 3 calibration stations.

### About the defects

**Q18. You found a coordinate bug after the preprint. Does that invalidate Phase 1?**
Coverage moved by at most 0.011 because calibration absorbs extra error. Accuracy and width changed a lot and are
reported with both frames. The weather distance effect disappeared, and the thesis reports that. A preprint update
is part of the pending preprint decision.

**Q19. And the stride issue?**
It can only make traffic accuracy and width look worse than they should, not better, and coverage barely moved
(0.882 to 0.895). It was found in exploratory work, is flagged in the report, and the pre-registered S0 test is the
first Phase 2 step. Original numbers are kept next to any re-run.

### About scale and architecture

**Q20. Why k-NN attention, and when does it help?**
Dense attention memory grows as N²; k-NN as N × k. Measured: 16.7 times less memory at 8,000 sensors, no advantage
below about 1,000. Output matches exact attention (pre-registered equivalence GO).

**Q21. Do you have coverage at 8,000 sensors?**
No real network that large was usable; synthetic networks up to 4,000 sensors gave 0.880 to 0.914. The memory claim
is about memory only. E tests coverage on the largest real network available.

**Q22. Why was the state-space block dropped?**
About twice as slow as the GRU on this hardware and the parity gate failed (error worse by 6.4, margin 2.4).

**Q23. Why does masked training help at Day 0 but not for warm sensors?**
With history available, the sensor's own past is the best predictor and the GRU already uses it. Without history,
only neighbours carry information, and masking is what trains the model to use them.

**Q24. Why is there no Day-0 gain on Delhi?**
Unresolved; plausible reasons are few stations (21 for training), daily resolution, and pollution being regionally
driven, so the IDW-interpolated GRU forecast is already close. It is reported as a negative control, and the
lifecycle claim is scoped to road networks.

### About the plan

**Q25. What if B fails?**
The fallback reports the measured curves and where validity or usefulness stops; the Day-0 result and Phase 1
calibration results stand independently.

**Q26. Why does D matter?**
Calibrated but wide intervals are useless if a seasonal rule gives narrower ones. On PeMS-BAY OmniST's intervals were
33% wider than seasonal-naive; the residual + scale head reversed that in feasibility (37% better interval score).

---

## 10. Glossary

| Term | Meaning |
|---|---|
| α (miscoverage) | 1 − target coverage; 0.10 here |
| ACI | Adaptive conformal inference: online adjustment of α to track coverage under shift |
| Ablation | Removing a component to measure its contribution |
| Calibration set | Held-out data used only to compute the conformal quantile |
| Chronological calibration | Quantile from errors of earlier windows only (forecast-time) |
| Cold start / Day 0 | Forecasting a sensor with no history |
| Conditional coverage | Coverage for each subgroup (station, time); not generally guaranteed |
| Coverage | Fraction of true values inside the interval |
| Exchangeability | Joint distribution unchanged by reordering; the assumption behind conformal guarantees |
| Expanding window | Calibration over all earlier errors |
| Forecast origin | Time the forecast is issued |
| GRU | Gated recurrent unit, a recurrent network cell |
| Hierarchical conformal (HCP) | Conformal with groups (stations) as the exchangeable unit |
| IDW | Inverse-distance weighting interpolation |
| Inductive | Works on nodes not seen in training |
| Interval (Winkler) score | Width plus 2/α times miss distance; lower is better |
| k-NN attention | Attention restricted to k nearest neighbours; cost N × k |
| Kriging | Spatial interpolation to unobserved locations |
| Leakage | Evaluation information reaching training or calibration |
| Marginal coverage | Coverage averaged over everything |
| Masked-station training | Hiding some stations' inputs in training to force spatial transfer |
| Nonconformity score | Measure of how unusual a prediction error is; here absolute or normalised error |
| Normalised score | Error divided by an estimated scale, giving adaptive widths |
| Parity / equivalence test | Showing a difference lies inside a pre-set margin |
| Persistence | Forecast equals last observed value |
| Pre-registration | Committing hypotheses and pass rules before running |
| Same-window calibration | Quantile from the same period being evaluated (not forecast-time) |
| Seasonal-naive | Forecast equals value one period ago |
| Shared GRU | One GRU applied to every sensor, no spatial input; the backbone control |
| Spacing | Median nearest-neighbour distance in a network |
| Split (station split) | Random assignment of stations to train / calibration / test |
| Split conformal | Conformal prediction with a separate calibration set |
| Stride | Step between the starts of consecutive training windows |
| Transductive | Works only on nodes seen in training |
| Warm-up | Period in which a new sensor accumulates history |

---

## 11. Reading list, in order

Read the first four before anything else. Reference numbers match `SEM3-PROGRESS-REPORT.md`, Section 8.

1. **Angelopoulos and Bates, "A Gentle Introduction to Conformal Prediction"** [5], arXiv:2107.07511. Sections 1
   to 3 and the part on conditional coverage. The single most useful reading.
2. **Vovk, Gammerman and Shafer, *Algorithmic Learning in a Random World*** [4]. Reference for exchangeability and
   the original theory; skim chapter 2.
3. **Wu et al., IGNNK** [3], AAAI 2021. The inductive kriging baseline; read for the masking idea and the problem
   setting.
4. **Lee, Barber and Willett, hierarchical conformal** [21], arXiv:2306.06342, and **Mallick et al., generalized
   hierarchical conformal** [22]. Why the station is the unit.
5. **Barber, Candès, Ramdas and Tibshirani, "Conformal prediction beyond exchangeability"** [15], and **Tibshirani
   et al., covariate shift** [14]. What happens when exchangeability fails; weighted conformal.
6. **Gibbs and Candès, "Adaptive Conformal Inference Under Distribution Shift"** (NeurIPS 2021, arXiv:2106.00170).
   Not yet in the reference list; needed for B.
7. **Xu et al., KITS** [23] and **Zhou et al., MoGERNN** [24]. Current inductive and Day-0 traffic forecasting.
8. **Yang et al., leakage-free evaluation for inductive kriging** [11]. Supports the evaluation argument.
9. **Angelopoulos et al., "Conformal Risk Control"** [19]. For alerts (F).
10. **Yu et al., STGCN** [1] and **Li et al., DCRNN** [2]. The transductive models you are contrasting with.
11. **Gu and Dao, Mamba** [6]. Only to answer why the state-space block was dropped.
12. **Liu et al., LargeST** [13] and **Wang et al., STGformer** [12]. Scale context.

Inside the repository, in order: `THESIS-OVERVIEW.md`, `SEM3-PROGRESS-REPORT.md` Sections 4.3 to 4.6,
`PRE-REGISTRATION-C1H.md`, `THESIS-COMPLETION-PLAN.md`, `phase2-omnist-scale/feasibility/REPORT-2.md`, and
`FINALIZATION-RECORD.md` for how each number was verified.
