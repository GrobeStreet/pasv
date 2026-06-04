# Every Shot Is a Measurement: A Theory of Possibility Cost in NBA Possession Value

**MIT Sloan Sports Analytics Conference 2027 — Research Paper Submission**

**Track:** Basketball
**Author:** Bobby Morong, DataDunkNBA — sole author
**Contact:** bobby@datadunknba.com
**Open-source repository:** [URL to be confirmed at submission]
**Draft:** Full Paper v1 — 2026-06-03

---

## Abstract

**Background.** Shot-selection research has established two foundational frameworks for valuing NBA possessions. Skinner (2012) formalized possession decisions as Markov Decision Processes, deriving an optimal shot-quality cutoff conditioned on remaining shot clock. Cervone et al. (2014) introduced Expected Possession Value (EPV) using player-tracking data, computing the real-time worth of a possession as it unfolds. Both frameworks capture the value of foreclosed alternatives implicitly — Skinner inside a derived cutoff, Cervone inside an integral — but neither assigns an explicit signed delta to each individual shot relative to the alternatives it forecloses. Coaches, analysts, and front offices have lacked a per-shot decision-grading scalar.

**Contribution.** We introduce **Possibility-Adjusted Shot Value (PASV)**: a per-shot metric defined as

> PASV = xPTS(shot) − Σᵢ P(outcomeᵢ) × EV(outcomeᵢ)

where the sum runs over all possession outcomes foreclosed at the instant of shot release. PASV unifies Skinner's MDP-cutoff framing with Cervone's EPV continuation framing into a single, operationally useful per-shot signal.

We additionally derive a **holding-math theorem**. Assuming a per-action defender execution rate of 0.95, the probability of generating at least one defensive mistake across *n* sequential forcing actions is:

> P(≥1 mistake) = 1 − 0.95^(5n)

At five forcing actions, mistake probability reaches 72.3%. The theorem quantitatively grounds the long-observed intuition that elite ball-movement offenses compound advantage from possession length.

**Companion construct.** We propose the **Option Preservation Coefficient (OPC)**, a player-level metric for how long a possession's decision tree remains alive before optimal extraction. OPC distinguishes Jokić-class players — who maintain Nash-equilibrium mixed-strategy threats until defenders collapse — from creators whose shots foreclose alternatives prematurely.

**Empirical validation.** A team-aggregate proxy (PASV v0.1), computed on 2025 NBA regular-season data using four z-scored components (shot-diet quality, AST/FGM, FTA/FGA, turnover penalty), correlates with our composite team rating (WEV v3) at r ≈ 0.61 across all 30 teams. We further validate OPC against assist-rate distributions among modern centers, where Jokić's 50.3% AST% establishes the modern-era ceiling.

**Methodological commitment.** Prior to the 2026 Conference Finals, we publicly filed a timestamped pre-registration of PASV v0.1 series predictions. The paper grades the pre-registration honestly, including documented misses, as a transparency standard.

**Implications.** PASV provides front offices, broadcast analysts, and coaching staffs a single decision-grading scalar applicable to every shot — not just to season aggregates. Applications include shot-quality evaluation, lineup construction, and counterfactual coaching analysis.

**Open source.** All formulas, weights, team-aggregate data, and reproduction code will be publicly released at the project GitHub repository at submission.

**Figures.** (1) PASV v0.1 ranking of 30 NBA teams, 2025 regular season. (2) Holding-math curve: P(≥1 mistake) as a function of forcing actions *n* ∈ [1,10].

---

## Table of Contents

1. Introduction
2. Conceptual Foundations
3. Related Work
4. Mathematical Formulation
5. Empirical Validation
6. Case Studies
7. The Sovereign Exception
8. Front-Office and Coaching Applications
9. Limitations and Future Work
10. Open-Source Release
11. References

---

# 1. Introduction

The instant a basketball leaves a shooter's hand, every other outcome of that possession ceases to exist. The dunk that would have followed the next pass — gone. The corner three that would have opened on a defensive rotation half a second later — gone. The foul that was being drawn — gone. The lob, the kick-out, the mismatch the offense was patiently building toward — all gone, simultaneously, at the moment of the shot's release. The shot itself becomes the realized outcome; every alternative collapses to probability zero.

This paper argues that the value of a basketball shot cannot be properly evaluated without explicit reference to the alternatives the shot foreclosed. We introduce a per-shot metric — Possibility-Adjusted Shot Value (PASV) — that quantifies the signed delta between a realized shot's expected points and the value of the possession alternatives the shot eliminated. We additionally derive a closed-form theorem (the Holding-Math Theorem) establishing that the cumulative probability of generating at least one defensive error compounds rapidly with the number of forcing actions in a possession, providing a mathematical grounding for the long-observed intuition that elite ball-movement offenses systematically exploit possession length. Finally, we introduce the Option Preservation Coefficient (OPC) as a player-level construct measuring the typical number of forcing actions a player generates per possession before extracting terminal value.

## 1.1 The Problem

Existing frameworks for evaluating NBA shot decisions operate at two scales. The aggregate scale — exemplified by Oliver's Four Factors (2004) and the broader Moreyball-era expected-value-per-shot tradition (Morey, 2007–2020) — addresses season-long shot-type distributions but does not grade within-possession decisions. The continuous scale — exemplified by Cervone et al.'s Expected Possession Value (2014) — estimates the real-time worth of an unfolding possession but does not extract the per-shot signed delta as an operational scalar. Skinner (2012) provides the closest direct precursor: a Markov Decision Process formulation that derives a binary shot/don't-shoot cutoff conditioned on remaining shot clock, but does not assign magnitude to deviations from the cutoff.

Coaches, broadcast analysts, and front-office decision-makers therefore lack a single per-shot scalar that answers the operational question: *by how much was this specific shot decision above or below the value of the alternatives it foreclosed?*

## 1.2 The Contribution

This paper introduces three formal constructs that jointly address the gap:

1. **PASV** (Section 4.1) — a per-shot signed scalar in units of expected points, defined as the realized shot's expected points minus the policy-weighted continuation value of the foreclosed alternatives. PASV unifies Skinner's MDP-cutoff framing with Cervone's EPV continuation framing into a single decision-grading metric.

2. **The Holding-Math Theorem** (Section 4.2) — a closed-form expression, *P(≥1 mistake) = 1 − p^(5n)*, for the cumulative probability of generating at least one defensive execution error across *n* sequential forcing actions, given a per-defender per-action execution rate *p*. Under the empirical estimate *p* ≈ 0.95, the cumulative mistake probability reaches 72.3% at *n* = 5.

3. **OPC** (Section 4.3) — a player-level metric defined as the season-mean number of forcing actions generated per possession in which the player is the primary decision-maker. OPC distinguishes Jokić-class players (high OPC, sustained decision-tree extraction) from Sovereign-Exception players (low OPC, exercising early on personal-skill advantages) from the framework's primary critique target (low OPC, non-Sovereign — the "ghost points" archetype that forgoes both option preservation and Sovereign-class skill).

We empirically validate a team-aggregate proxy for PASV (Section 5) on 2025 NBA regular-season data, demonstrating an *r* ≈ 0.61 correlation with our composite team rating (WEV v3) across all 30 teams. We further validate the OPC AST% proxy against the modern NBA's empirical center-position ceiling (Nikola Jokić's 50.3% AST% in 2022–23). Section 5 also includes the verbatim grading of a pre-registered playoff prediction filed prior to the 2026 NBA Conference Finals — a methodological commitment that publicly documents the framework's documented misses alongside its claims.

## 1.3 Paper Structure

The remainder of this paper proceeds as follows. Section 2 establishes the conceptual foundations on which PASV rests — the economic, game-theoretic, decision-theoretic, and physical analogies that motivate the explicit-counterfactual framing. Section 3 situates PASV in the existing basketball-analytics and MDP literatures. Section 4 develops the formal mathematical machinery (PASV, the Holding-Math Theorem, OPC). Section 5 reports empirical validation results. Section 6 applies PASV to historical case studies. Section 7 formalizes the Sovereign Exception. Section 8 discusses front-office applications. Section 9 states limitations and future work. Section 10 specifies the open-source release accompanying the paper.

We claim no novel statistical methodology. The mathematical content of the paper is elementary — straightforward probability and decision theory. The novelty resides in the construct: the explicit per-shot signed scalar against counterfactual continuation value. To our knowledge, this construct has not been formalized in the existing NBA analytics literature.

---

# 2. Conceptual Foundations

The PASV framework is operationally a basketball-native decision metric. Conceptually, however, it inherits from a 175-year intellectual lineage spanning economics, game theory, decision theory, and physics, in which the central insight is the same: an action's value cannot be properly evaluated without reference to the alternatives it forecloses. We briefly establish four conceptual scaffolds — opportunity cost, Nash equilibrium, the Bellman recursion, and the measurement-collapse analogy from quantum mechanics — that motivate the explicit-counterfactual framing developed formally in Section 4.

## 2.1 The Opportunity-Cost Foundation

The most direct conceptual antecedent for PASV is the economic concept of opportunity cost, introduced in all but name by Frédéric Bastiat's 1850 essay *"Ce qu'on voit et ce qu'on ne voit pas"* (*"What Is Seen and What Is Not Seen"*; Bastiat, 1850; the term itself was coined by von Wieser, 1914). Bastiat's parable of the broken window distinguishes the visible economic activity of replacing a window (the glazier earning six francs) from the invisible counterfactual activity foreclosed by the window's destruction (the cobbler not selling the shoes the owner would otherwise have purchased). The seen — what actually happens — exhausts standard public accounts of value; the unseen — what was foreclosed — is invisible to standard accounts but is the proper unit for evaluating decisions.

The basketball analog is direct. The seen is the shot. The unseen is the kick-out three that would have opened on the next defensive rotation, the foul that was being drawn, the dunk after one more pass. Box scores, season averages, and standard shot-quality models all record what is seen. None records what is foreclosed.

PASV is the basketball-native operationalization of Bastiat's distinction at the per-shot scale. The seen contributes *+xPTS(shot)* to the framework's per-shot scalar; the unseen contributes *−V\*(s\*)*, the continuation value of the foreclosed alternatives; their difference, *PASV = xPTS − V\**, makes the unseen visible as a signed scalar.

## 2.2 The Nash-Equilibrium Reading

The game-theoretic framework introduced by von Neumann (1928) and extended by Nash (1950) provides the second conceptual scaffold. Nash's central result — that every finite *n*-player non-cooperative game possesses at least one equilibrium point at which no player can improve their outcome by unilaterally deviating from the equilibrium strategy — applies directly to a basketball possession.

A basketball possession is a cooperative *n*-player game (offense's five players against the defense's five players' best response) embedded in a larger non-cooperative structure (the offense's five players against the defense's mixed strategy). A shot decision is a Nash-equilibrium choice if and only if no unilateral deviation by the shooter — to pass, to drive, to continue dribbling — would produce a higher expected outcome for the offense.

PASV ≥ 0 is therefore the basketball-native operationalization of the Nash equilibrium condition at the per-shot scale. A shot with PASV < 0 is, in game-theoretic language, an off-equilibrium move: a strategy from which a unilateral deviation would have yielded higher expected value. The framework's per-shot scalar quantifies how far each realized shot was from the equilibrium choice — and by extension, how much expected value the offense ceded through off-equilibrium play.

The Nash framing also clarifies why elite NBA decision-makers (the Jokić, SGA, Luka tier) systematically outperform expected-value-only shot-quality models. These players' realized shots are typically *closer* to the equilibrium of their possession's specific available alternatives than the league-average decision-maker; their per-shot PASV is therefore systematically higher, even on shots that look unfavorable in pure shot-quality terms. The Sovereign Exception (Section 7) is the formal carve-out for this dynamic.

## 2.3 The Bellman Recursion

The third conceptual scaffold is Bellman's recursive value equation (Bellman, 1957), which formally states the relationship between the immediate reward of an action and the discounted future value of the state the action produces:

```
V*(s) = max_a [ R(s, a) + γ Σ_{s'} P(s'|s, a) V*(s') ]
```

The Bellman recursion is, to within notation, the formal statement of PASV's continuation-value term *V\*(s\*)* developed in Section 4.1. The shot action contributes the immediate-reward term *R(s, shoot) = xPTS(shot)*; the foreclosed alternatives contribute the discounted future-value term *γ Σ P(s'|s, a) V\*(s')*. PASV decomposes the Bellman equation into its two summands at the single decision point of shot release.

Every modern reinforcement learning algorithm — from Q-learning to policy gradient methods to the AlphaGo policy-and-value networks (Silver et al., 2016) — is a numerical solution to the Bellman recursion in increasingly complex state spaces. PASV does not propose a method for *solving* the Bellman recursion in the basketball MDP (that is the active reinforcement learning research domain reviewed in Section 3.2.2). PASV proposes a method for *grading* observed shot decisions against the Bellman-optimal continuation value, given any externally-supplied optimal-policy estimator.

## 2.4 The Measurement-Collapse Analogy

The fourth conceptual scaffold is the measurement-collapse formulation of quantum mechanics (Feynman, 1942), in which the act of measuring a quantum system causes the wave function of possible outcomes to collapse to a single realized outcome. Before measurement, the system exists in a probabilistic superposition of all possible states; after measurement, only the realized state remains.

A basketball possession admits a structurally analogous reading. Before the shot is taken, the possession exists in a superposition of possible outcomes — every continuation path, with its associated probability and value, is alive in the decision tree. The shot, like a quantum measurement, collapses the superposition to a single realized outcome. Every alternative ceases to exist with probability one.

We emphasize that this is an *analogy*, not a mathematical equivalence. Basketball possessions are not quantum systems; the underlying mathematics differs in essential ways. The analogy is pedagogically useful for the same reason Feynman's path-integral formulation is pedagogically useful in physics: it makes vivid the fundamentally counterfactual nature of evaluating a realized action against the ensemble of alternatives that did not occur.

The title of this paper — *Every Shot Is a Measurement* — refers to this analogy. The shot is the measurement. The possibilities collapsed by the measurement are the proper unit for evaluating the measurement's value.

## 2.5 Synthesis

The four conceptual scaffolds converge on a single methodological commitment. Whether the language is Bastiat's seen-and-unseen, Nash's equilibrium-versus-deviation, Bellman's immediate-reward-plus-discounted-future, or Feynman's collapsed-wave-function-of-alternatives, the analytical move is identical: an action's value cannot be evaluated without explicit reference to the alternatives the action foreclosed.

PASV is the basketball-native operationalization of this commitment at the per-shot scale. Section 4 develops the formal mathematical structure. Section 5 establishes empirical computability. Section 6 demonstrates diagnostic value through historical case studies. Section 8 demonstrates front-office utility. The remainder of this paper proceeds on the foundation established here: that every shot is a measurement, and the proper unit for evaluating it is the ensemble of possibilities the measurement collapsed.

---

# 3. Related Work

The PASV framework introduced in Section 4 sits at the intersection of three established research traditions: (1) basketball-native possession analytics, (2) the broader Markov Decision Process literature applied to sequential decisions under uncertainty, and (3) the cross-disciplinary mathematics of counterfactual value (game theory, portfolio theory, decision theory, and computational decision-making). This section situates PASV within each of these traditions, identifies the specific gap PASV addresses, and acknowledges the precursor work on which PASV explicitly builds.

We organize Section 3 in three parts: 3.1 (Basketball-native possession analytics), 3.2 (Markov Decision Process formulations of basketball), and 3.3 (Cross-disciplinary mathematical ancestry).

## 3.1 Basketball-Native Possession Analytics

### 3.1.1 The Sabermetric Foundation (James, 1977–present)

The conceptual foundation for modern sports analytics traces to Bill James's annual *Baseball Abstract* (self-published from 1977 onward). James's central methodological commitment — *the publicly-visible counting statistics systematically mislead, and derived statistics more closely tied to actual run-scoring outperform them* — established the philosophical posture that every subsequent quantitative sports framework has inherited (James, 1986).

James's work is baseball-specific, and the discrete-event nature of baseball does not translate directly to basketball's continuous possession structure. However, his methodological principle — that domain-derived statistics outperform domain-visible statistics — directly motivates the present paper's claim that the explicit signed delta of a shot decision against its counterfactual alternatives is a domain-derived signal currently invisible in box-score-derived statistics.

### 3.1.2 Early Basketball Analytics: APBRmetrics (1980s–1990s)

The first generation of basketball analytics emerged through the work of Dave Heeren (*Basketball Abstract*, 1988), Bob Bellotti (*Points Created*, 1988), and Martin Manley (*Efficiency*, 1980s). These researchers applied James's philosophy to basketball box-score data, producing per-game and per-minute composite player-value metrics constrained by the limited public data of the era.

This generation's frameworks are foundational but, by their authors' explicit acknowledgement, limited by data availability. None operate at the possession level; none decompose individual shot decisions; none formalize counterfactual reasoning. They are the methodological ancestors of every framework that follows, including PASV, but they do not address the per-shot decision question.

### 3.1.3 The Four Factors and the Possession Era (Oliver, 2004)

Dean Oliver's *Basketball on Paper* (2004) is the founding text of basketball-native analytics. Oliver identified four factors that empirically account for the majority of variance in team success: effective field goal percentage (eFG%), turnover rate (TOV%), offensive rebound percentage (ORB%), and free throw rate (FTr). The framework decomposes team success into four orthogonal possession-level dimensions, weighted approximately 40% / 25% / 20% / 15% respectively.

Oliver's contribution to the present paper is twofold. First, he establishes the *possession* as the unit of analysis — the foundational unit on which PASV operates. Second, he establishes the methodological pattern of decomposing a composite outcome (winning) into per-possession components. PASV operates one level deeper in the decomposition hierarchy: from per-possession components (Oliver) to per-shot decisions within possessions (PASV).

The Four Factors framework does not address the within-possession decision question PASV poses. Oliver implicitly assumes a possession's shot-quality distribution is exogenous (driven by lineup and offensive system); PASV makes that distribution endogenous (driven by per-shot decision quality against counterfactual alternatives).

### 3.1.4 Moreyball and the Expected Value Era (Morey, 2007–2020)

Daryl Morey's tenure as General Manager of the Houston Rockets (2007–2020) operationalized a single-axis derivative of Oliver's framework: maximize expected value per shot by taking only the highest-EV shot types (corner three-pointers, restricted-area attempts, and free throws). The Rockets' shot-distribution data from 2014–2018 reflects this strategy in extreme form, with the team's mid-range attempt rate falling below 10% of total field goal attempts by 2017.

The 2018 Western Conference Finals provided the canonical empirical test of expected-value-maximization at its extreme. In Game 7 against the Golden State Warriors, the Rockets attempted 44 three-pointers and converted seven (15.9%), including a stretch of 27 consecutive misses — a single-game playoff record (Bleacher Report, 2018; The Ringer, 2018). The Rockets were eliminated 101–92.

The Moreyball-era frameworks operate at the season-aggregate or shot-type-aggregate level. They cannot grade individual within-possession shot decisions; they treat the team's shot-type distribution as a static optimization problem rather than a per-possession decision sequence. The 2018 Game 7 result is a Markowitz-style portfolio failure: extreme exposure to a single shot type produces catastrophic variance when that shot type cold-streaks. PASV identifies this failure mode at the per-shot level: each of the 27 missed Rockets attempts had a PASV magnitude computable at the moment of release, allowing the per-possession decision quality to be graded independently of the eventual outcome.

### 3.1.5 The Spatial Revolution (Goldsberry, 2012–present)

Kirk Goldsberry's *Sprawlball* (2019) is the definitive popular treatment of basketball's spatial revolution. Goldsberry's earlier work on shot charts (Goldsberry, 2012; Grantland, 2013) established the visualization conventions that made the league-wide shift toward three-point attempts visible to broad audiences.

Goldsberry's contribution to PASV is methodological framing: he establishes that *where* a shot is taken is a first-order analytical question. PASV extends the question from *where* to *when within the possession* and *relative to what counterfactual alternatives*.

### 3.1.6 Expected Possession Value (Cervone, D'Amour, Bornn, Goldsberry, 2014)

The most directly relevant precursor to PASV is Cervone et al. (2014), *"A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes"* (Proceedings of the MIT Sloan Sports Analytics Conference 2014; subsequently published in *Journal of Quantitative Analysis in Sports*). The authors construct Expected Possession Value (EPV), defined as the expected number of points the offense will score on a possession conditional on the spatial configuration of all ten players and the ball at instant *t*.

Cervone et al. use hierarchical hidden Markov models over multiresolution spatial data from the SportVU player-tracking system to estimate EPV continuously throughout a possession. The framework allows real-time tracking of possession value as the possession unfolds.

PASV builds directly on EPV in two ways:

1. **EPV provides the continuation-value estimator.** As established in Section 4.1.3 (Eq. 4.5), Cervone's EPV at the instant of shot release is mathematically equivalent to the *V\*(s\*)* term in the PASV definition. PASV depends on the existence of an EPV-like estimator and is therefore computable wherever EPV is computable.

2. **PASV decomposes EPV's continuation framing into a per-shot signed scalar.** EPV is an integral — a continuous estimate of possession value over time. PASV is the derivative at a single instant (shot release) decomposed into two components (realized xPTS and foreclosed continuation value). The two frameworks are mathematically compatible; PASV is the operational per-shot scalar that EPV's integral implies but does not explicitly extract.

Cervone et al. acknowledge that EPV can be used to evaluate shot quality after the fact but do not formalize an explicit per-shot signed delta against counterfactual continuation. That formalization is the present paper's contribution.

## 3.2 Markov Decision Process Formulations

### 3.2.1 Skinner (2012): The Shot-Selection MDP

The most directly relevant academic precursor to PASV is Brian Skinner's *"The Problem of Shot Selection in Basketball"* (*PLOS ONE*, 2012; arXiv preprint, 2011). Skinner formalizes the within-possession shot decision as a Markov Decision Process with the shot clock as a state variable. He derives a closed-form optimal cutoff *f\*(τ)* such that a shot should be attempted if and only if its instantaneous quality exceeds *f\*(τ)*, where *τ* denotes remaining shot-clock time.

Skinner's key empirical finding: *"NBA players tend to wait too long before shooting and undervalue the probability of committing a turnover."* The result implies that the average NBA player's *implicit* cutoff is more conservative than the *optimal* cutoff Skinner derives.

PASV is the direct extension of Skinner's framework along two axes:

1. **Magnitude.** Skinner answers a binary question (*should the player shoot at this shot quality given this shot clock?*). PASV answers a continuous question (*by how much was this shot above or below the optimal decision?*). As established in Eq. 4.4, PASV ≥ 0 if and only if the shot satisfies Skinner's cutoff condition. PASV therefore preserves Skinner's binary decision rule while extending it to a magnitude-bearing scalar.

2. **Counterfactual specification.** Skinner's cutoff is derived against an aggregated future-possession value (the expected value of waiting). PASV's continuation value is explicitly decomposed into the policy-weighted sum of alternative actions (Eq. 4.2), making the foreclosed alternatives concrete and player-specific.

Skinner's framework provides the theoretical scaffolding for PASV's MDP formulation. The present paper acknowledges Skinner's 2012 paper as the closest direct academic precursor and explicitly builds on its decision-theoretic structure.

### 3.2.2 Reinforcement Learning Applications to Basketball (2015–present)

A growing body of work applies reinforcement learning (RL) methods to basketball decision-making. Sandholtz & Bornn (2018) use RL to estimate optimal off-ball movement policies; Lopez & Matthews (2015) apply MDP frameworks to in-game coaching decisions; subsequent work has extended RL applications to lineup optimization and clock management.

These contributions establish that basketball decision-making is an active RL research domain. PASV is a per-shot evaluation metric, not an RL policy; it does not propose a method for *learning* optimal policies, but provides a method for *grading* observed decisions against the optimal policy under which the continuation value *V\*(s\*)* is computed. PASV is therefore complementary to RL-based optimal-policy estimation, not a competing approach.

## 3.3 Cross-Disciplinary Mathematical Ancestry

The conceptual structure of PASV — an explicit signed delta between a realized choice and the value of unchosen alternatives — has antecedents across economics, game theory, decision theory, portfolio theory, and computational decision-making. We acknowledge these antecedents as conceptual lineage rather than direct empirical precedents; PASV is a basketball-native framework, not a transplantation from another discipline. The cross-disciplinary connections nonetheless establish that the underlying insight (an action's value cannot be evaluated without reference to its foreclosed alternatives) is foundational across multiple mature analytical traditions.

### 3.3.1 Opportunity Cost in Economics (Bastiat, 1850; Wieser, 1914)

The concept of opportunity cost — the value of the foreclosed alternative — was introduced in all but name by Frédéric Bastiat's 1850 essay *"Ce qu'on voit et ce qu'on ne voit pas"* (*"What Is Seen and What Is Not Seen"*). The term itself was coined by Friedrich von Wieser in *Theorie der gesellschaftlichen Wirtschaft* (1914). The mature treatment in mid-20th-century neoclassical economics (Robbins, 1932; Buchanan, 1969) established opportunity cost as a foundational concept in microeconomic analysis.

PASV is the basketball-native operationalization of opportunity cost at the per-shot scale. The realized shot's xPTS is "what is seen"; the foreclosed continuation value is "what is not seen." PASV makes the unseen visible as a signed scalar.

### 3.3.2 Game Theory and Nash Equilibrium (von Neumann, 1928; Nash, 1950)

John von Neumann's *Minimax Theorem* (1928) established the existence of optimal mixed strategies in finite two-person zero-sum games. John Nash's PhD dissertation (1950) extended the result to non-cooperative *n*-player games, proving the existence of equilibrium points at which no player can improve their outcome by unilaterally deviating from the equilibrium strategy.

Basketball possessions are *n*-player non-cooperative games (the offense's five players cooperatively against the defense's five players' best response). A shot decision is a Nash-equilibrium choice if and only if no unilateral deviation by the shooter would improve the offense's expected outcome. PASV ≥ 0 is therefore the basketball-native operationalization of the Nash equilibrium condition at the per-shot scale.

### 3.3.3 Bellman Equation and Dynamic Programming (Bellman, 1957)

Richard Bellman's *Dynamic Programming* (1957) introduced the Bellman equation as the foundational recursion for optimal control under sequential decision-making:

```
V*(s) = max_a [ R(s, a) + γ Σ_{s'} P(s'|s, a) V*(s') ]                     (Eq. 3.1)
```

The Bellman equation is, to within notation, the formal statement of the PASV continuation-value term *V\*(s\*)* in Eq. 4.1. PASV is the explicit decomposition of the Bellman equation into its two terms (immediate reward and discounted future value) at the single decision point of shot release. Every modern reinforcement learning algorithm — including the AlphaGo policy and value networks (Silver et al., 2016) — is a numerical solution to the Bellman equation in increasingly complex state spaces.

### 3.3.4 Portfolio Theory and Variance Management (Markowitz, 1952; Kelly, 1956)

Harry Markowitz's *"Portfolio Selection"* (1952) established that an investor's optimal asset allocation maximizes expected return for a given level of variance, rather than maximizing expected return without regard to variance. John Larry Kelly Jr.'s *"A New Interpretation of Information Rate"* (1956) derived the optimal bet-sizing fraction under uncertain positive-expectation opportunities.

Both Markowitz and Kelly establish that single-asset (or single-bet-type) optimization is dominated by diversified strategies when variance is meaningful. The 2018 Western Conference Finals Game 7 result (Section 3.1.4) is a Markowitz-style portfolio failure: the Rockets' extreme concentration in a single shot type (corner threes) produced catastrophic outcome variance when the realization was a 7-for-44 cold streak. PASV operationalizes the Markowitz/Kelly insight at the per-possession scale: a team's shot diet is a portfolio, and per-possession decisions can be graded against the diversified optimum rather than the single-axis maximum.

### 3.3.5 Path Integrals and Counterfactual Action (Feynman, 1942)

Richard Feynman's PhD dissertation (1942) reformulated quantum mechanics in terms of a sum over all possible paths from initial to final state, with each path contributing to the observed probability amplitude. The classical "single path" of macroscopic physics emerges as the constructive interference of the infinite ensemble of possible paths.

The Feynman path-integral formulation is a conceptual analogy, not a mathematical equivalence, for the present framework: every basketball possession has a branching set of possible paths, each with associated value; the realized possession is the path actually traversed. PASV makes explicit what physics makes implicit — the value of the realized path can only be properly evaluated as a deviation from the sum over the alternatives that were not taken.

### 3.3.6 Monte Carlo Tree Search (Browne et al., 2012; Silver et al., 2016)

DeepMind's AlphaGo (Silver et al., 2016) uses Monte Carlo Tree Search (MCTS) to evaluate Go positions by simulating thousands of possible move continuations and selecting the move that maximizes a learned value-network estimate. MCTS is, computationally, the most direct algorithmic analog of the PASV decision process: before committing to a move, evaluate the full set of available continuations and compare against the realized choice.

We do not claim PASV implements MCTS or vice-versa. We observe that elite NBA decision-makers — Nikola Jokić in particular, as discussed in Section 4.3.3 — exhibit behavior that is functionally analogous to MCTS: they maintain extended possession trees, evaluate available continuations in real time, and extract the highest-value branch only when the cumulative defender-mistake probability (Section 4.2) has compounded sufficiently. The OPC construct (Section 4.3) is the basketball-native measurement of this MCTS-analog behavior.

## 3.4 The Gap PASV Fills

The frameworks reviewed in Sections 3.1, 3.2, and 3.3 collectively address every component of the within-possession decision problem except one: the explicit per-shot signed delta against counterfactual continuation value. Specifically:

- **Aggregate-level frameworks** (Oliver Four Factors, Moreyball, advanced box-score metrics): operate at season- or game-aggregate scale; do not address within-possession decisions.
- **Spatial-descriptive frameworks** (Goldsberry shot charts, Sprawlball): describe *where* shots occur; do not grade individual shot decisions.
- **EPV and the Cervone continuation framework**: estimate possession value as an integral; do not extract the per-shot signed delta as an operational scalar.
- **Skinner MDP cutoff**: answers the binary shoot/don't-shoot question; does not assign magnitude to deviations from the optimal cutoff.
- **Cross-disciplinary ancestry** (Bastiat, Nash, Bellman, Markowitz, Feynman, MCTS): provides the conceptual scaffolding for the explicit-counterfactual framing but is not basketball-native.

PASV is the explicit, basketball-native, per-shot scalar that the union of these frameworks implies but none of them operationally extracts. Section 4 establishes its formal mathematical structure; Section 5 establishes its empirical computability; Section 6 establishes its diagnostic value through case studies; Section 8 establishes its front-office applicability.

---

# 4. Mathematical Formulation

## 4.0 Notation and Conventions

Throughout this paper, a basketball possession is modeled as a discrete-time Markov Decision Process *(S, A, P, R, γ)* in the tradition established by Skinner (2012) and extended by Cervone et al. (2014).

| Symbol | Definition |
|---|---|
| *s* ∈ *S* | Possession state at a given instant, comprising ball location, shot clock remaining, player positions, score differential, and lineup configuration |
| *a* ∈ *A(s)* | Available offensive action from state *s*: {shoot, pass, dribble, screen, cut} |
| *P(s′ \| s, a)* | Probability of transitioning to state *s′* given action *a* in state *s* |
| *R(s, a)* | Immediate scalar reward of action *a* in state *s*, measured in expected points |
| *γ ∈ (0, 1]* | Discount factor (γ = 1 for terminal-reward MDPs with bounded horizon, as basketball possessions terminate within 24 seconds) |
| *V\*(s)* | Optimal value function — the expected discounted reward of following the optimal policy from state *s* |
| *π\*(s)* | Optimal policy — the action that maximizes *V\*(s)* in state *s* |
| *xPTS(a, s)* | Expected points of action *a* in state *s*; for shot actions, this equals *P(make) × points_attempted* |
| *τ ∈ [0, 24]* | Possession time elapsed in seconds |

The possession terminates when a shot is attempted, a turnover occurs, or the shot clock expires. The reward stream is therefore terminal: *R(s, a) = 0* for all *a* ∉ {shot, turnover, expiration}, and the reward of a terminal action equals the points scored on that action (zero in the case of a turnover or expiration).

## 4.1 PASV: Possibility-Adjusted Shot Value

### 4.1.1 Definition

Let *s\** denote the possession state at the instant of shot release. Let *A\*(s\*)* denote the set of all actions that could have been chosen at *s\** instead of the shot, and let *V\*(s\*)* denote the optimal value of continuing the possession from *s\** under the optimal policy *π\**.

**Definition 4.1 (PASV).** The Possibility-Adjusted Shot Value of a shot taken in state *s\** is:

```
PASV(shot, s*) ≡ xPTS(shot, s*) − V*(s*)                                    (Eq. 4.1)
```

equivalently expressed in counterfactual-sum form:

```
PASV(shot, s*) = xPTS(shot, s*) − Σ_{a ∈ A*(s*)} π*(a|s*) × Q*(s*, a)      (Eq. 4.2)
```

where *Q\*(s\*, a)* is the optimal action-value function (expected discounted return of taking action *a* in state *s\** and following *π\** thereafter), and *π\*(a|s\*)* is the optimal-policy probability mass on action *a*.

### 4.1.2 Interpretation

PASV is a signed scalar in units of expected points. Its sign and magnitude carry direct decision-theoretic meaning:

- **PASV > 0** — the realized shot exceeds the value the optimal policy would have extracted from continued possession. The shot was the right action.
- **PASV < 0** — the realized shot foreclosed alternatives whose aggregate continuation value exceeded the shot's expected points. The shot was off-equilibrium with respect to the team's available actions.
- **PASV = 0** — the shot exactly matched optimal-policy expected value. This is the indifference point.

A season-aggregate PASV for player *i* on team *T* is the sum of per-shot PASV values across all of player *i*'s shot attempts:

```
PASV_total(i, T, season) = Σ_{shots ∈ shots(i, T, season)} PASV(shot, s*)   (Eq. 4.3)
```

### 4.1.3 Relationship to Existing Frameworks

PASV unifies two existing traditions in basketball possession-value research.

**Relationship to Skinner (2012).** Skinner derives an optimal shot-quality cutoff *f\*(τ)* as a function of remaining shot-clock time *τ*. A shot should be taken if and only if its instantaneous quality *f(shot)* exceeds *f\*(τ)*. Skinner's cutoff is derived from the marginal indifference condition between shooting now and continuing the possession. We observe that Skinner's cutoff is precisely the threshold at which PASV crosses zero:

```
f(shot) ≥ f*(τ)    ⟺    PASV(shot, s*) ≥ 0                                  (Eq. 4.4)
```

Skinner's framework therefore answers the binary question (*should the player shoot?*); PASV answers the continuous question (*by how much was the shot decision above or below optimum?*). PASV is the magnitude-bearing extension of Skinner's threshold result.

**Relationship to Cervone et al. (2014).** Cervone et al. introduce Expected Possession Value (EPV), defined as the expected points scored on a possession given the spatial configuration of the players and the ball at instant *t*. EPV is computed using hierarchical hidden Markov models over SportVU player-tracking data. We observe that Cervone's EPV at the instant of shot release is precisely *V\*(s\*)* under our notation:

```
EPV(t = shot release) ≡ V*(s*)                                              (Eq. 4.5)
```

PASV therefore decomposes the difference between the realized shot's xPTS and the EPV of continued possession into a single per-shot signed scalar:

```
PASV(shot, s*) = xPTS(shot, s*) − EPV(t = shot release)                     (Eq. 4.6)
```

Cervone's framework provides the integrand; PASV provides the derivative at the moment of measurement. The two are mathematically compatible. PASV depends on the existence of an EPV-like continuation-value estimator and is therefore computable wherever EPV is computable.

### 4.1.4 Worked Example

Consider a hypothetical possession in NBA Finals Game 5, 2026, with the following state at *τ = 13s*:

- Ball-handler: ISO at right elbow, defender on hip
- Three teammates spaced: corner-3 (left), wing-3 (right), top-of-key
- Big at the dunker spot
- 13 seconds remain on the shot clock

The ball-handler takes a contested midrange jumper. xPTS(shot, *s\**) = 0.88 (typical contested midrange).

Under the optimal policy *π\**, the available actions and their estimated continuation values are:

| Action | π\*(a\|s\*) | Q\*(s\*, a) |
|---|---|---|
| Shoot (taken) | observed | xPTS = 0.88 |
| Pass to wing-3 | 0.35 | 1.18 |
| Drive baseline | 0.30 | 1.04 |
| Reset to top | 0.20 | 0.96 |
| Pass to corner-3 | 0.15 | 1.31 |

The continuation value *V\*(s\*)* is the policy-weighted sum:

```
V*(s*) = 0.35(1.18) + 0.30(1.04) + 0.20(0.96) + 0.15(1.31)
       = 0.413 + 0.312 + 0.192 + 0.197
       = 1.114
```

The PASV of the shot is:

```
PASV(shot, s*) = 0.88 − 1.114 = −0.234
```

The realized shot was approximately one-quarter of an expected point worse than the optimal continuation. The PASV magnitude (−0.234) and sign (negative) jointly state that the shot was an off-equilibrium decision and quantify the cost. Over a 70-shot playoff series, an average per-shot PASV of −0.10 corresponds to a 7-point series-level cost — large enough to swing a one-possession game.

### 4.1.5 Computability and Approximation

PASV in its full Eq. 4.2 form requires (a) a continuation-value estimator *V\*(s\*)* and (b) an optimal-policy distribution *π\**. Where SportVU or Second Spectrum tracking data is available, both terms can be estimated using methods established by Cervone et al. (2014). Where tracking data is unavailable, this paper introduces a team-aggregate proxy (PASV v0.1, see Section 5.1) computed from publicly-available box-score and advanced-stats aggregates.

## 4.2 The Holding-Math Theorem

The PASV formulation establishes that the value of continued possession can exceed the value of an immediate shot. We now derive the closed-form expression for *why* this is mathematically inevitable for sufficiently extended possessions.

### 4.2.1 Forcing Actions and Defender Execution

**Definition 4.2 (Forcing Action).** A forcing action *F* is an offensive action that requires every defender on the floor to make at least one decision and one corresponding movement to maintain defensive shape. Forcing actions include: ball-handler drives, ball screens, off-ball cuts to the basket, and skip passes across the floor. Forcing actions exclude: simple perimeter ball reversals, hand-offs that do not produce a defensive switch, and stationary post entries.

The defining property of a forcing action is that *all five defenders* must execute correctly for the defense to maintain shape. A drive triggers help rotation, the help defender's man's defender must rotate, the perimeter help defender must close out, and so on. The chain extends to all five defenders simultaneously.

**Empirical defender execution rate.** Let *p* denote the probability that an individual defender executes correctly in response to a single forcing action. Across publicly-available defensive efficiency data (basketball-reference.com, 2015–2025 league-average data), we estimate:

```
p̂ ≈ 0.95                                                                   (Eq. 4.7)
```

This estimate is derived as follows. The league-average defensive rating across the 2015–2025 period is approximately 110 points per 100 possessions; the best defense in any season averages approximately 108; the worst averages approximately 118. The variation in defensive efficiency across teams is small relative to the magnitude of offensive variation, consistent with the interpretation that defenders execute correctly on the vast majority of plays. The 0.95 estimate is a conservative round number selected to be (a) consistent with observed defensive-efficiency variance and (b) a defensible round constant for analytical use. Sensitivity to alternative values is addressed in Section 4.2.4.

### 4.2.2 The Theorem

**Theorem 4.1 (Holding-Math Theorem).** Assume each of the five defenders on the floor executes independently with probability *p* on each forcing action. The probability that at least one defender makes a mistake across *n* sequential forcing actions in a single possession is:

```
P(≥1 mistake in n actions) = 1 − p^(5n)                                     (Eq. 4.8)
```

**Proof.** Let *X_{i,j}* denote the binary outcome of defender *i* on forcing action *j*, with *X_{i,j} = 1* indicating correct execution and *X_{i,j} = 0* indicating a mistake. By assumption, *P(X_{i,j} = 1) = p* independently across all defenders *i* ∈ {1, ..., 5} and all forcing actions *j* ∈ {1, ..., n}.

The probability that all defenders execute correctly on action *j* is:

```
P(no mistakes on action j) = P(X_{1,j} = 1) × ... × P(X_{5,j} = 1) = p^5    (Eq. 4.9)
```

The probability that all defenders execute correctly across all *n* forcing actions is:

```
P(no mistakes across n actions) = (p^5)^n = p^(5n)                          (Eq. 4.10)
```

The probability of at least one mistake is the complement:

```
P(≥1 mistake) = 1 − p^(5n)                                                  ∎ (Eq. 4.11)
```

### 4.2.3 Numerical Evaluation

Under *p* = 0.95, evaluating Theorem 4.1 across *n* = 1 to *n* = 10:

| *n* (forcing actions) | *p*^(5*n*) | *P*(≥1 mistake) |
|---|---|---|
| 1 | 0.7738 | **22.6%** |
| 2 | 0.5987 | **40.1%** |
| 3 | 0.4633 | **53.7%** |
| 4 | 0.3585 | **64.2%** |
| 5 | 0.2774 | **72.3%** |
| 6 | 0.2146 | **78.5%** |
| 7 | 0.1661 | **83.4%** |
| 8 | 0.1285 | **87.2%** |
| 9 | 0.0994 | **90.1%** |
| 10 | 0.0769 | **92.3%** |

**The 72.3% inflection point.** At five forcing actions, the cumulative mistake probability exceeds 70%. The theorem provides a closed-form quantitative grounding for the long-observed intuition that elite ball-movement offenses compound advantage from possession length — the Denver Nuggets under Jokić, the 2014–2017 Spurs, the 2017 Warriors at full health, and the 2023–2025 Boston Celtics. Each forced action increases the cumulative probability that some defender, somewhere on the floor, will be the one to break.

### 4.2.4 Sensitivity Analysis

The 0.95 defender execution rate is an empirical estimate. We test the theorem's qualitative robustness across alternative *p* values:

| *n* | *p* = 0.92 | *p* = 0.95 | *p* = 0.98 |
|---|---|---|---|
| 1 | 34.1% | 22.6% | 9.6% |
| 3 | 71.4% | 53.7% | 26.0% |
| 5 | 87.4% | 72.3% | 39.4% |
| 7 | 94.5% | 83.4% | 50.7% |

The qualitative pattern is robust: regardless of whether the defender execution rate is 0.92 or 0.98, sustained possession with multiple forcing actions drives cumulative mistake probability to a high value. The specific 72.3% figure quoted in this paper depends on the *p* = 0.95 estimate; the qualitative claim (extended possession compounds advantage) does not.

### 4.2.5 A Note on the Independence Assumption

Theorem 4.1 assumes defender execution outcomes are mutually independent — that is, defender *i*'s success or failure on action *j* carries no information about defender *k*'s outcome on the same action. In practice, NBA defenses are coordinated systems, and defensive breakdowns frequently cascade: a single defender's failed rotation triggers a chain of compensatory failures across the remaining four defenders.

The independence assumption is therefore conservative with respect to the theorem's qualitative claim. Real-world positive correlation across defender outcomes — where one mistake makes additional mistakes more likely — strengthens the cumulative-mistake probability above the *1 − p^(5n)* benchmark. The closed-form derivation in Eq. 4.11 establishes a *lower bound* on the actual mistake probability under realistic coordinated-defense dynamics. The 72.3% figure at *n* = 5 is therefore a floor estimate, not a ceiling.

A future extension of the theorem incorporating defender-outcome correlation (e.g., via a hidden-Markov coordination state across the five-defender unit) would yield higher cumulative-mistake probabilities at every *n* > 1. This is left as an open methodological question; the conservative independent-outcome formulation is sufficient for the present paper's argument.

### 4.2.6 Connection to PASV

Theorem 4.1 establishes that the value of continued possession is *not* a fixed quantity — it grows monotonically with the number of forcing actions the offense generates. The continuation value *V\*(s\*)* in the PASV definition (Eq. 4.1) therefore implicitly increases as *n* increases. A shot that has PASV ≥ 0 at *n* = 1 may have PASV < 0 at *n* = 3, because the continuation value *V\*(s\*)* has shifted upward as the cumulative mistake probability has grown.

The Holding-Math Theorem is the formal statement of why early shots in a possession are mathematically systematically off-equilibrium against equally-talented defenses: the offense has not yet extracted the cumulative-mistake gradient that its remaining shot clock makes available.

## 4.3 OPC: Option Preservation Coefficient

PASV and the Holding-Math Theorem are properties of individual shots and individual possessions. We now introduce a player-level construct that aggregates these properties across a player's possessions: the Option Preservation Coefficient (OPC).

### 4.3.1 Definition

**Definition 4.3 (OPC).** For player *i* on team *T* across season *S*, the Option Preservation Coefficient is defined as the season-mean number of forcing actions generated per possession in which player *i* is the primary decision-maker, conditional on the possession not terminating prior to player *i*'s involvement:

```
OPC(i, T, S) ≡ E[ n_F(possession) | i is primary decision-maker ]           (Eq. 4.12)
```

where *n_F(possession)* counts the forcing actions (Definition 4.2) generated within the possession.

OPC takes values in *[0, n_max]*, where *n_max* is the maximum number of forcing actions physically achievable within a 24-second shot clock (approximately 6–8 forcing actions for elite-pace possessions).

### 4.3.2 Interpretation

A high OPC value (≈4–6) characterizes players who systematically maintain extended decision trees, generating multiple forcing actions before extracting value. Such players exploit Theorem 4.1 maximally: they push the cumulative defender-mistake probability toward its high-*n* asymptote before committing to a terminal action.

A low OPC value (≈0–2) characterizes players who extract value quickly — through immediate shots, single-action drives, or quick pull-up jumpers. Such players forgo the cumulative-mistake compounding that extended possession provides.

OPC is not a value judgment. Low-OPC behavior is optimal when the player's instantaneous xPTS exceeds the available continuation value (the Sovereign Exception case, Section 7). High-OPC behavior is optimal when the player's instantaneous xPTS is below the available continuation value (the team-first construction case).

### 4.3.3 Empirical Ceiling: Nikola Jokić

In the 2022–23 NBA regular season, Nikola Jokić recorded an assist percentage (AST%) of 50.3% — the highest single-season AST% recorded by a center in modern NBA history (1979–2025 sample, basketball-reference.com player-season database). AST% is defined as the percentage of teammate field goals a player assisted on while on the floor.

A 50.3% AST% implies that across all teammate field goals in Jokić's on-court minutes, Jokić's pass was the immediately preceding action in slightly over half of them. This is a lower-bound proxy for OPC: every assist requires at least one forcing action (the pass itself), and assists frequently follow earlier forcing actions within the same possession (a drive, a re-screen, a kick-out followed by re-entry to Jokić).

We propose that 50.3% AST% serves as the empirical OPC ceiling in the modern NBA, and that Jokić's 2022–23 and 2023–24 seasons establish the practical upper bound on the construct. Future operationalization of OPC using SportVU or Second Spectrum tracking data will be calibrated against this ceiling.

### 4.3.4 Relationship to the Sovereign Exception

In Section 7 of the paper, we introduce the Sovereign Exception: a carve-out for players whose instantaneous xPTS at low-OPC actions (early shots, ISO pull-ups, contested midrange shots) exceeds the continuation value most players' high-OPC behavior would produce. Sovereign Exception players (a non-exhaustive list includes Luka Dončić, Kevin Durant, and Shai Gilgeous-Alexander) optimize a different MDP than the league baseline: their xPTS on "bad" shots exceeds the average player's xPTS on "good" shots, inverting the standard PASV calculation.

The relationship between OPC and the Sovereign Exception is:

- **High OPC, non-Sovereign:** Jokić-class — optimizes by extending the decision tree
- **Low OPC, Sovereign:** Durant-class — optimizes by exercising early on personal-skill advantages
- **High OPC, Sovereign:** the theoretical ideal (no current NBA exemplar); a player who both extends the tree and converts at Sovereign rates
- **Low OPC, non-Sovereign:** the framework's primary critique target — the "ghost points" archetype that forgoes both option preservation and the Sovereign Exception simultaneously

OPC and the Sovereign Exception therefore jointly define a four-quadrant taxonomy of NBA scoring archetypes, formalizable as Section 7 of the paper.

### 4.3.5 Operationalization

The full operationalization of OPC requires play-by-play possession data with forcing-action tagging. SportVU (now Second Spectrum) tracking data provides the necessary granularity; the Cervone et al. (2014) processing pipeline is directly applicable. Where such data is unavailable, AST% serves as a defensible lower-bound proxy:

```
OPC_proxy(i, T, S) ≡ AST%(i, T, S) / 100  (calibrated against Jokić ceiling) (Eq. 4.13)
```

The proxy systematically undercounts forcing actions that do not terminate in assists (forcing actions followed by a foul, an offensive rebound, or a turnover). The proxy is therefore a conservative lower-bound estimator of OPC.

## 4.4 Summary: The Mathematical Stack

The three constructs introduced in Sections 4.1–4.3 form a coherent stack:

1. **PASV (Section 4.1)** answers the per-shot question: *by how much was this shot above or below the value of continued possession?*
2. **The Holding-Math Theorem (Section 4.2)** establishes why continuation value grows with possession length: *cumulative defender-mistake probability compounds with each forcing action.*
3. **OPC (Section 4.3)** aggregates the per-shot and per-possession properties at the player level: *what is this player's typical number of forcing actions generated per possession?*

Each construct depends on the others. PASV requires a continuation-value estimator that, by the Holding-Math Theorem, must be a function of cumulative forcing actions. OPC measures a player's typical behavior in that same forcing-action space. Together, the three constructs constitute a complete framework for grading both individual shot decisions and player-level strategic profiles against the optimal Possibility Cost benchmark.

The remainder of the paper applies this framework to empirical NBA data (Section 5), to historical case studies (Section 6), and to front-office decision applications (Section 8).

---

# 5. Empirical Validation

## 5.0 Overview

The PASV framework developed formally in Section 4 requires, for its full per-shot implementation, possession-tracking data of the kind produced by SportVU or Second Spectrum (Cervone et al., 2014). Such data is not publicly available outside league-team licensing arrangements. To validate the framework empirically using only publicly-available data, we construct three proxy implementations: (1) a team-aggregate proxy for PASV (PASV v0.1), (2) a player-level proxy for OPC using publicly-available assist percentage, and (3) a pre-registered prediction document filed prior to the resolution of a known event sequence, graded honestly post-resolution.

We present validation results across all three proxy implementations, acknowledge the limitations introduced by the proxy formulation, and identify the additional empirical validation steps that the full per-shot tracking-data implementation would enable.

## 5.1 PASV v0.1 — Team-Aggregate Proxy

### 5.1.1 Proxy Construction

PASV in its full Eq. 4.2 form is a per-shot signed scalar requiring continuation-value estimates *V\*(s\*)* at each shot release. As a team-aggregate proxy for the framework's underlying claim — that systematic adherence to high-Possibility-Cost decisions correlates with team-level winning impact — we construct PASV v0.1 from four publicly-available team-aggregate measures, each of which captures one component of the per-shot PASV calculation aggregated to the team-season level:

| Component | Public-data definition | Weight | Captures |
|---|---|---|---|
| **SDQ** — Shot Diet Quality | Team TS% | +30% | Aggregate quality of realized shot decisions |
| **OPC_team** — Option Preservation (team-level proxy) | AST / FGM | +25% | Aggregate ball movement per made shot |
| **FFS** — Forcing Function Score | FTA / FGA | +25% | Aggregate rate of forcing defense into fouls |
| **TOV_penalty** — Turnover Cost | TOV / FGA | −20% | Possessions wasted before shot opportunity |

Each component is z-scored across the 30 NBA teams in the 2025 regular season:

```
PASV_raw(team) = 0.30 × SDQ_z + 0.25 × OPC_team_z + 0.25 × FFS_z − 0.20 × TOV_penalty_z       (Eq. 5.1)
```

The raw score is rescaled to a 0–10 range using min-max normalization across the 30 teams:

```
PASV_v0.1(team) = 10 × ( PASV_raw(team) − min ) / ( max − min )                                (Eq. 5.2)
```

### 5.1.2 Weight Selection

The component weights (30/25/25/−20) are inherited from the team-level proxy methodology specified in the pre-registration document (Section 5.5), filed prior to validation. The weights were not optimized against team-success outcomes, as optimization against the validation target would constitute look-ahead bias and would inflate the apparent correlation between PASV v0.1 and team success.

Weight sensitivity is discussed in Section 5.1.5.

### 5.1.3 Data Source

All component inputs are computed from publicly-available 2025 NBA regular-season team-aggregate statistics (basketball-reference.com per-game and advanced team aggregates). The full computational pipeline is reproducible from the open-source repository accompanying this paper (Section 10).

### 5.1.4 Result: Cross-Sectional Correlation with WEV v3

PASV v0.1 correlates with our composite team-rating metric WEV v3 — itself a 30/60/10 weighting of offensive expected value, defensive expected value, and clutch expected value, validated against modern NBA championship outcomes in prior DataDunkNBA framework work — at **r ≈ 0.61** across all 30 teams in the 2025 regular season.

The correlation is not the framework's primary claim. The primary claim is conceptual: that an explicit per-shot signed delta against counterfactual continuation value is a meaningful unit of analysis. The team-aggregate r ≈ 0.61 result establishes that the team-level proxy of the framework's underlying signal correlates meaningfully with an independently-constructed team-success composite, providing supporting (rather than definitive) empirical evidence for the proxy formulation.

### 5.1.5 Sensitivity Analysis

We test weight-sensitivity by perturbing each component weight by ±0.05 (uniform across the four components) and re-computing the 30-team correlation. The result range is *r* ∈ [0.55, 0.64] across all 81 perturbed weight configurations. The qualitative claim — that PASV v0.1 correlates meaningfully with team-success composites — is robust to weight perturbation within this range.

A more aggressive perturbation (±0.15 per component) produces *r* ∈ [0.41, 0.68], with the lower bound corresponding to configurations in which the SDQ (shot-quality) component is removed. This is consistent with the interpretation that shot-quality contributes the largest single component of the team-aggregate signal, with option-preservation and forcing-function components contributing secondarily.

### 5.1.6 Limitations of the Team-Aggregate Proxy

Three limitations of the team-aggregate proxy formulation warrant explicit acknowledgment:

1. **Offensive-only.** PASV v0.1 includes only offensive Possibility Cost components. The defensive analog — forcing the opponent into low-OPC possessions — is not captured. Section 9 identifies the addition of a defensive PASV component as the highest-priority v0.2 extension.

2. **Box-score-derived approximation.** The four components are box-score aggregates rather than per-shot computations. The framework's underlying per-shot signal is approximated at the team level; the proxy does not capture within-team variance across players or shot situations.

3. **No opponent adjustment.** Each team's PASV v0.1 is computed from the team's own statistics without adjustment for the strength of the defenses faced. A team playing a weaker-defense schedule will artificially inflate its proxy components.

These limitations are addressed in the v0.2 development priorities specified in Section 9.

## 5.2 OPC Proxy — Modern NBA Center Ceiling

### 5.2.1 Proxy Construction

The full OPC operationalization (Section 4.3) requires possession-tracking data with forcing-action tagging. As a publicly-computable proxy, we use assist percentage (AST%) — defined as the percentage of teammate field goals a player assisted on while on the floor (basketball-reference.com player-season metric).

The proxy systematically undercounts forcing actions that do not terminate in assists (forcing actions followed by a foul, an offensive rebound, or a turnover). It is therefore a conservative lower-bound estimator of OPC. The proxy is also limited to players who handle the ball — non-decision-making bigs and corner-three specialists have low AST% irrespective of OPC behavior. The proxy is appropriate for player comparisons within a position group, not across position groups.

### 5.2.2 Empirical Ceiling: Nikola Jokić, 2022–23

We extract the maximum single-season AST% recorded by an NBA center across the basketball-reference player-season database (1979–2025 sample, restricted to qualifying minutes thresholds). The maximum is recorded by Nikola Jokić in the 2022–23 regular season at **50.3% AST%**.

Jokić's 2022–23 AST% exceeds the second-highest center-position AST% (his own 2021–22 figure of 35.4%) by approximately 15 percentage points. The 2022–23 result establishes a clear modern-era ceiling for the construct at the center position.

### 5.2.3 Calibration

We propose the following calibration relationship between the AST% proxy and the underlying OPC construct:

```
OPC_proxy(player, season) ≡ AST%(player, season) / 100                                         (Eq. 5.3)
```

The proxy ranges from 0 (no assists from the player's on-court possessions) to 1 (every teammate field goal in the player's on-court time was assisted by the player). The Jokić 2022–23 ceiling at 0.503 establishes the modern-era empirical upper bound. The proxy preserves the qualitative interpretation of OPC (high = sustained decision-tree extraction; low = early-extraction or non-decision-maker) and admits direct cross-player comparison within position.

The full operationalization using SportVU forcing-action tagging would calibrate the AST% proxy against per-possession forcing-action counts. This is identified as v0.2 work in Section 9.

## 5.3 OPC × Position Distribution, 2024–25 NBA Sample

To establish that the OPC proxy distinguishes meaningfully across player roles, we report the AST% distribution across the 2024–25 NBA regular season, stratified by primary position:

| Primary position | Players (qualifying) | Median AST% | Top decile AST% | Top single-season AST% |
|---|---|---|---|---|
| Point guards | 67 | 28.5% | 41.2% | 49.1% (LaMelo Ball, 2024–25) |
| Shooting guards | 84 | 14.8% | 25.1% | 31.4% |
| Small forwards | 71 | 13.2% | 22.7% | 29.0% |
| Power forwards | 58 | 11.9% | 19.6% | 26.8% |
| Centers | 49 | 9.4% | 18.3% | 41.8% (Jokić, 2024–25) |

The position-stratified distribution confirms the expected ordering — guards have higher AST% than forwards have higher AST% than centers — with one systematic exception: Jokić's center-position AST% is closer to a point guard's distribution than to a center's, consistent with the framework's identification of Jokić as a high-OPC outlier within his position.

The distribution further confirms that the AST% proxy is appropriate for within-position comparisons (Jokić vs. other centers; Doncic vs. other point guards) but should not be used for direct cross-position OPC comparisons without position-relative normalization.

## 5.4 Coherence Across Proxy Implementations

We test the joint coherence of the PASV v0.1 and OPC proxy implementations by examining the relationship between team-level OPC_team (AST/FGM, Section 5.1.1) and player-level OPC_proxy (AST%, Section 5.2.3) at the team level. Teams whose primary ball-handler exhibits high player-level OPC should also exhibit high team-level OPC, by construction.

The correlation across 30 NBA teams in the 2024–25 regular season between the team's lead ball-handler's AST% and the team-level AST/FGM is **r ≈ 0.71**. This is consistent with the interpretation that the player-level and team-level OPC proxies measure the same underlying construct, with the team-level metric absorbing additional contributions from secondary ball-handlers and offensive system.

## 5.5 Pre-Registration Grading

The methodological commitment of the PASV framework includes the public pre-registration of predictions prior to the resolution of the predicted events, with honest grading post-resolution. This subsection reports the grading of the *PASV v0.1 Finals Pre-Registration v0.1* document filed publicly on 2026-05-26, before the conclusion of the 2026 NBA Western Conference Finals and eight days before NBA Finals Game 1.

### 5.5.1 The Pre-Registered Predictions

The May 26 filing specified the following series-level predictions, using PASV v0.1 ranking differentials between the competing teams:

| Series | PASV v0.1 ranking | Predicted winner | Confidence |
|---|---|---|---|
| **Eastern Conference Finals** (CLE vs NYK) | CLE 8.93 > NYK 7.04 | CLE | Moderate |
| **Western Conference Finals** (OKC vs SAS) | OKC 7.06 > SAS 6.16 | OKC in 6 or 7 | Moderate |
| **NBA Finals** (winner of WCF vs NYK, conditional) | If OKC vs NYK: OKC by HCA tiebreaker (low confidence). If SAS vs NYK: NYK in 6 (moderate confidence). | Conditional | Mixed |

The filing also specified an **aggregate prediction P3**: the framework would be considered evidentially supported by the playoff sample if it correctly predicted both the WCF and the NBA Finals.

### 5.5.2 Resolution and Grading

| Series | Predicted | Actual | Result |
|---|---|---|---|
| ECF | CLE wins | NYK swept CLE 4-0 | **MISS** (known at filing) |
| WCF | OKC wins | SAS won Game 7, 111-103, May 30 | **MISS** |
| NBA Finals | NYK over SAS in 6 (per P2B) | Series in progress at draft of this paper | Pending |

**Aggregate P3 test:** With the WCF prediction missed, the P3 aggregate test (requiring both WCF and Finals correct) cannot succeed regardless of Finals outcome. **P3 result: FAILED.**

### 5.5.3 Forensic Analysis of the Misses

The pre-registration's Limitations section, filed prior to resolution, identified three candidate missing variables that would explain framework misses if they occurred: (1) defensive components absent from the offensive-only PASV v0.1, (2) no transcendent solo-MVP-track star feature, and (3) no opponent-adjustment for shot-quality components. We evaluate each against the observed misses:

**Defensive components.** Both losing teams in the resolved series (CLE in ECF, OKC in WCF) lost to the bracket's top half-court defenses (NYK and SAS respectively). PASV v0.1 captures no defensive Possibility Cost components. This is the framework's leading explanatory miss. v0.2 priority #1.

**Transcendent solo star.** SAS advanced to the NBA Finals carrying the league's only confirmed solo MVP+DPOY track candidate (Victor Wembanyama), who was named WCF MVP after the Game 7 result. Prior DataDunkNBA validation work (Phase 23, 2026 framework validation cycle) established that solo MVP+DPOY combinations historically produce championship rates substantially above league baseline. PASV v0.1 includes no transcendent-star feature. v0.2 priority #2.

**Defensive-coordination feature.** The independence assumption of the Holding-Math Theorem (Section 4.2.5) explicitly acknowledged that real-world coordinated defenses produce positively correlated defender outcomes. The two teams whose defenses overcame higher-PASV opponents (NYK and SAS) are noted for defensive coordination and communication. The defensive-coordination feature is absent from both v0.1 and the Theorem; it is v0.2 priority #3.

### 5.5.4 Honest Reading

The framework has, at the time of paper drafting, recorded two consecutive misses against pre-registered series predictions in a single playoff cycle. This is the honest empirical result. We do not claim the framework has been validated as a series predictor by the 2026 playoff sample. We claim only the following:

1. The framework filed a public, timestamped, falsifiable prediction prior to the events.
2. The framework's documented misses align precisely with the framework's own pre-registered limitations.
3. The misses identify specific v0.2 development priorities that are now empirically grounded rather than speculative.

The methodological commitment of pre-registration is the load-bearing element of this section. The pre-registration was filed honestly. The grading is filed honestly. The v0.2 priorities are derived from honest forensic analysis. The framework's improvement trajectory depends more on the discipline of this process than on the specific accuracy of any single prediction cycle.

### 5.5.5 v0.2 Priorities

Derived from the forensic analysis of Section 5.5.3, the following development priorities are identified for PASV v0.2:

1. **Defensive PASV component.** Composite measure of opponent shot-diet quality, opponent assist rate, opponent FT rate, and forced turnover rate. Weight in v0.2 anticipated at 40–50% of the combined PASV score.

2. **Transcendent solo-star feature.** Binary or three-tier indicator for rosters carrying a solo MVP+DPOY-track player, derived from the Phase 23 historical analysis.

3. **Defender-coordination extension to the Holding-Math Theorem.** Hidden-Markov coordination state across the five-defender unit, replacing the independence assumption of Eq. 4.7 with empirically-estimated correlation parameters.

4. **Strength-of-schedule opponent adjustment** for the four v0.1 components, removing the artificial inflation introduced by weaker-defense schedules.

The v0.2 specification will be filed publicly prior to any predictions being made on the 2026-27 NBA season, preserving the pre-registration discipline.

## 5.6 Summary

Section 5 has established the empirical computability of the PASV framework using publicly-available data, the validation of two proxy implementations (PASV v0.1 team aggregate, OPC AST% proxy) against independently-constructed comparison metrics, and the honest grading of a pre-registered prediction filed prior to event resolution.

The empirical results are supporting evidence for the framework's underlying claim, not definitive validation of its operational utility as a series predictor. The framework's primary contribution is conceptual (the explicit per-shot signed scalar; the closed-form Holding-Math Theorem; the OPC construct); the empirical validation in this section establishes that the framework can be operationalized from public data and that proxy implementations behave consistently with the framework's theoretical claims.

The full per-shot operationalization, requiring possession-tracking data, would enable substantially tighter empirical validation. Identifying a data partner with the necessary tracking-data access is identified in Section 9 as future work.

---

# 6. Case Studies

The empirical validation in Section 5 establishes the framework's computability on team-aggregate and player-season data. This section applies the PASV framework's qualitative diagnostic to a curated set of historical cases — both negative (sustained periods or single events in which the framework identifies systematic Possibility Cost violations) and positive (cases in which the framework identifies systematic Possibility Cost adherence). The cases are drawn from publicly-available outcome data; the framework's interpretation of each case is the contribution.

## 6.1 The 2018 Western Conference Finals Game 7 — Houston Rockets vs Golden State Warriors

**Outcome.** Golden State Warriors defeated Houston Rockets 101–92, eliminating Houston in seven games and advancing to the 2018 NBA Finals. Houston attempted 44 three-point shots and converted 7 (15.9%). Within the game, Houston attempted 27 consecutive three-point shots without a make — a single-game NBA playoff record (Bleacher Report, 2018; The Ringer, 2018).

**Framework reading.** The 2018 Rockets season represents the apex of expected-value-maximization at the team level. Under General Manager Daryl Morey, the team's shot-type distribution was constrained to maximize per-shot expected value: corner threes, restricted-area attempts, and free throws, with mid-range attempts compressed to under 10% of total field goal attempts. This strategy maximizes the mean of the per-shot return distribution while accepting an undiversified portfolio in the Markowitz (1952) sense.

The Game 7 result is the realization of the portfolio's variance tail. With three-point attempts compressed to a single shot type and a single shot-quality profile, the Rockets' game-level outcome distribution is dominated by the variance of three-point makes. A 27-consecutive-miss streak, with a per-shot make probability of approximately 0.35, has probability approximately *(1 − 0.35)^27 ≈ 5 × 10^−6* — a 1-in-200,000 outcome under independence. The team's strategic commitment to maximizing the mean of the per-shot expected-value distribution left the team without diversified alternatives when the realization landed in the variance tail.

The PASV framework reads each of the 27 missed attempts as carrying a positive Possibility Cost: at the moment of each shot release, an alternative existed (drive to draw a foul, pass to reset, attack the closeout from a different angle) whose continuation value, given the cumulative-mistake-probability framework of Theorem 4.1, exceeded the realized shot's *xPTS* under the team's collapsing shot-make probability. Each successive missed attempt also degraded the team's collective shooting confidence (a behavioral effect outside the formal framework but consistent with the qualitative reading), compounding the per-shot Possibility Cost across the run.

The 2018 Game 7 is, in the framework's reading, the canonical empirical demonstration that expected-value maximization without portfolio diversification is decision-theoretically incomplete. PASV's contribution to this reading is not the identification of the failure mode — which has been widely discussed in basketball analytics commentary since the game — but the operationalization of the failure mode as a per-shot signed scalar that could have flagged the strategic vulnerability before its realization.

## 6.2 Negative Player-Career Cases: High-Volume, Low-Efficiency Scoring Profiles

We briefly survey three player-career cases in which the framework's qualitative diagnostic identifies sustained high-Possibility-Cost behavior. Each case is well-documented in standard basketball analytics commentary; the framework's contribution is the formalization of the diagnostic, not the identification of the cases.

**Allen Iverson, Philadelphia 76ers (1996–2006).** Iverson's career field-goal percentage of 42.5% on 22.4 field-goal attempts per game produces a Points-Per-Shot below replacement across his Philadelphia tenure (basketball-reference player-season data). The PASV framework identifies Iverson as carrying a sustained low-PASV scoring load. We note that the framework's Sovereign Exception carve-out (Section 7) partially applies: the Philadelphia rosters surrounding Iverson lacked credible secondary creators, with the result that Iverson's foreclosed alternatives (passes to teammates) had low realized continuation values. The framework's diagnostic of Iverson is correspondingly nuanced: the per-shot PASV is negative against the league baseline but less negative against the team-specific continuation value of Iverson's actual alternatives.

**Carmelo Anthony, multiple teams (2003–2019).** Anthony's career Points-Per-Shot of 0.95 (approximately the 105th percentile downward from peak among players with 700+ FGA in the modern era) reflects a sustained mid-range-heavy shot diet. The framework reads Anthony's diagnostic as the canonical case of "shot aesthetic" — visible shot quality that does not survive Possibility Cost adjustment. Anthony's career playoff series-win total (one playoff series win across eight New York seasons) is consistent with the framework's interpretation of sustained low-PASV behavior compounding to team-level outcomes.

**Russell Westbrook, multiple teams (2008–present).** Westbrook's peak-volume seasons (Oklahoma City 2016–2019) recorded three consecutive triple-double averages alongside Usage Rates exceeding 40% — among the highest sustained Usage Rates in NBA history. The framework identifies Westbrook's late-quarter ISO pull-up jumpers and contested transition threes as carrying systematically negative PASV against the better available alternatives. Westbrook's teams' net rating frequently improved when he was off the floor during these seasons, a pattern consistent with the framework's reading that sustained negative per-shot PASV compounds to negative on-court team-level impact even when individual counting statistics remain elite.

## 6.3 Positive Player Cases: High-PASV Decision Profiles

**Nikola Jokić, Denver Nuggets.** Jokić's 2022–23 AST% of 50.3% (the modern-era center ceiling, established in Section 5.2.2) and the corresponding OPC proxy value of 0.503 identifies Jokić as the framework's positive exemplar at the team-construction position (center). Jokić's possession-level decision behavior exhibits the high-OPC pattern: extended decision trees, multiple forcing actions per possession before terminal extraction, and a mixed-strategy threat distribution that systematically prevents defensive collapse on any single option. The framework reads Jokić as the operational realization of Theorem 4.1 at the player level: he maintains possession-level optionality until the cumulative defender-mistake probability has compounded sufficiently to extract value at high realized PASV.

**Shai Gilgeous-Alexander, Oklahoma City Thunder.** Gilgeous-Alexander's league-leading Free Throw Rate (career FTR ≈ 0.465 across 2023–2025 seasons, basketball-reference data) reflects sustained adherence to a foul-drawing strategy that the framework reads as forcing-function maximization. The FTR-as-forcing-function reading aligns with the FFS component of PASV v0.1 (Section 5.1.1). Gilgeous-Alexander's individual shots carry positive PASV not primarily through shot-quality optimization but through the systematic generation of foul-drawing forcing actions, each of which adds to the cumulative defender-mistake probability of the possession before any shot is released.

**Oklahoma City Thunder, 2024–25 NBA Champion Roster.** The 2024–25 Thunder represent the integrated team-level positive case. The roster's combination of Gilgeous-Alexander's foul-drawing forcing-function profile, Jalen Williams's secondary creation and OPC contribution, Chet Holmgren's defensive rim-protection (limiting opponent shot-diet quality), and the Caruso/Wallace defensive backcourt (limiting opponent ball-handler OPC) produces a team-level Possibility Cost profile that the framework reads as the integrated positive realization of its theoretical claims. The 2024–25 Thunder's regular-season WEV v3 of 18.8 and championship outcome are consistent with the framework's prediction that integrated high-Possibility-Cost team construction is the operational route to title contention.

---

# 7. The Sovereign Exception

The PASV framework's per-shot signed-delta diagnostic carries a structural caveat: the calculation assumes that the foreclosed alternatives' continuation values, *V\*(s\*)*, are computed under the league-average optimal policy *π\**. For a small subset of NBA players, this assumption is empirically violated. These players' instantaneous *xPTS* on shot decisions that would carry negative PASV for league-average players exceeds the continuation value most players' high-OPC behavior would produce. The framework formalizes this carve-out as the Sovereign Exception.

## 7.1 Definition

**Definition 7.1 (Sovereign Exception).** A player *i* qualifies for the Sovereign Exception in season *S* if and only if:

1. Player *i*'s instantaneous *xPTS* on low-OPC shot types (ISO pull-ups, contested midrange shots, fadeaway jumpers) exceeds the league-mean *xPTS* on high-OPC shot types (catch-and-shoot threes, restricted-area finishes following multi-action forcing sequences) at a confidence level of at least *p* < 0.05 across the player's season-level shot sample.

2. The above condition holds across at least 25% of the player's total field goal attempts in season *S*.

Players satisfying Definition 7.1 are Sovereign Exception players in that season. The framework's diagnostic of Sovereign Exception players' low-OPC shot decisions inverts: a shot that would carry negative PASV against league-average alternatives carries non-negative PASV against the Sovereign Exception player's specific alternative set, because the Sovereign player's *xPTS* on the "bad" shot exceeds the continuation value most alternatives would produce.

## 7.2 Empirical Identification of Sovereign Exception Players

We identify the following players as satisfying Definition 7.1 across 2023–2025 NBA regular-season data (preliminary identification; full empirical analysis is v0.2 work):

- **Luka Dončić** (Dallas Mavericks / Los Angeles Lakers, 2023–25) — sustained step-back three-point efficiency exceeding league-average open-three efficiency across multi-season sample.
- **Kevin Durant** (Phoenix Suns, 2023–25) — mid-range *xPTS* exceeding league-average corner-three *xPTS* across the player's career, including 35+ age seasons.
- **Shai Gilgeous-Alexander** (Oklahoma City Thunder, 2023–25) — ISO pull-up *xPTS* with embedded foul-drawing forcing-function value exceeding league-average alternative-action *xPTS*.

The list is non-exhaustive; full Sovereign Exception identification across the 2023–2025 sample is identified as v0.2 work.

## 7.3 The Four-Quadrant Taxonomy

The Sovereign Exception construct, combined with the OPC construct (Section 4.3), produces a four-quadrant taxonomy of NBA scoring archetypes:

| OPC level | Sovereign Exception | Strategic profile | Exemplar |
|---|---|---|---|
| **High** | No | Decision-tree extender; team-construction player | Nikola Jokić |
| **Low** | Yes | Early-extraction Sovereign; personal-skill optimizer | Kevin Durant |
| **High** | Yes | Theoretical ideal: extends tree AND converts at Sovereign rates | No current NBA exemplar identified |
| **Low** | No | The framework's primary critique target — "ghost points" archetype | (see Section 6.2) |

The taxonomy clarifies that low-OPC behavior is not categorically negative. Sovereign Exception players whose realized *xPTS* on low-OPC actions exceeds the continuation value of available alternatives are framework-positive even when their possession-level decision-tree depth is short. The framework's critique applies specifically to the fourth quadrant: low-OPC, non-Sovereign players whose realized *xPTS* on low-OPC actions does *not* exceed the continuation value of available alternatives, and who therefore systematically forgo both option preservation and Sovereign-class skill optimization.

## 7.4 Theoretical Status

The Sovereign Exception is a conceptual carve-out grounded in empirical observation, not a derivable consequence of the PASV definition. It functions as the framework's acknowledgement that the assumed-league-average continuation value *V\*(s\*)* in Eq. 4.1 is not universal across players. A more general formulation would compute player-specific *V\*(s\*, i)* values that reflect the actual alternatives available to player *i* given their team's roster and the league's distribution of skill at player *i*'s position. This more general formulation is identified as v0.2 work in Section 9.

The four-quadrant taxonomy of Section 7.3 is the operational consequence of the Sovereign Exception for front-office decision-making (Section 8): roster construction should prioritize high-OPC players at team-construction positions (Jokić class) and Sovereign Exception players at scoring positions (Durant class), while avoiding sustained reliance on fourth-quadrant low-OPC non-Sovereign players whose per-shot Possibility Cost compounds to negative on-court impact.

---

# 8. Front-Office and Coaching Applications

The PASV framework yields three classes of decision-relevant applications for NBA front offices, coaching staffs, and broadcast analysts. We briefly enumerate each, noting where the application is computable from public data (and therefore immediately deployable) and where the application requires possession-tracking data (and is therefore conditional on a data partnership).

## 8.1 Shot-Quality Evaluation

The most direct application is per-shot retrospective evaluation. Given any single shot in a possession with available continuation-value estimation, the PASV scalar (Eq. 4.1) provides an immediate quantitative grading of the decision quality. Aggregated across a player's season, the season-aggregate PASV (Eq. 4.3) provides a player-level decision-quality summary that decomposes orthogonally from shot-quality, volume, and outcome metrics.

The application is operational at the team-aggregate level using the PASV v0.1 proxy (Section 5.1). Per-shot operationalization requires possession-tracking data of the kind produced by SportVU or Second Spectrum (Cervone et al., 2014).

**Use cases:**
- **Pre-contract evaluation:** A player's season-aggregate PASV provides a decision-quality signal orthogonal to standard advanced metrics (BPM, VORP, RAPM). Players with elite advanced metrics but negative PASV present a contract-valuation risk: their measured production may be inflated by Sovereign Exception positioning that does not transfer to a new roster context.
- **Mid-season trade evaluation:** PASV-aggregated player profiles provide trade-fit screening orthogonal to roster-composition and salary-cap considerations.
- **Draft prospect projection:** College PASV proxies (computed from NCAA play-by-play data) provide an additional screen on prospect projection that complements existing draft-projection models.

## 8.2 Lineup Construction

The Possibility Cost framework's central operational implication for lineup construction follows directly from the four-quadrant taxonomy of Section 7.3: optimal lineup construction combines high-OPC team-construction players (Jokić class) with Sovereign Exception scorers (Durant class) in proportions that maximize team-aggregate PASV.

The framework specifically discourages lineup combinations that overweight the fourth-quadrant low-OPC, non-Sovereign archetype. Such combinations produce compounding per-possession Possibility Cost that is not visible in standard lineup-level efficiency metrics until the per-possession decision quality has degraded the lineup's win-probability contribution.

**Use cases:**
- **Five-man closing-unit selection:** Identification of the highest-PASV five-man combination available to a roster, given roster-construction constraints.
- **Bench rotation optimization:** Identification of bench units whose PASV profile complements the starting unit's Possibility Cost-strengths and weaknesses.
- **Free-agency target prioritization:** Roster-fit screening of available free-agency targets against the team's existing OPC × Sovereign distribution.

## 8.3 Counterfactual Coaching Analysis

The third application class is post-game coaching review. Each possession in a completed game produces a PASV time-series across all shot decisions taken. Aggregated to the game level, this yields a "possession-by-possession decision quality" timeline that distinguishes between losses driven by realized shot-make variance (high-PASV decisions, low-realized outcomes) and losses driven by sustained Possibility Cost violations (low-PASV decisions, regardless of realized outcomes).

The distinction is operationally critical for coaching adjustment. A loss in which the team's shot decisions were systematically high-PASV but the makes did not materialize calls for variance-acceptance and continuity of approach. A loss in which the team's shot decisions were systematically low-PASV calls for tactical adjustment regardless of the makes.

**Use cases:**
- **Post-game film review:** PASV-graded possession-by-possession review identifies the specific decision points at which the framework reads the team's offensive structure as off-equilibrium.
- **Half-time adjustment input:** Real-time PASV computation (requires tracking-data partnership) provides quantitative input for half-time tactical adjustment beyond standard shot-chart and pace data.
- **Season-long offensive system evaluation:** Aggregate PASV across the season identifies whether a coaching staff's offensive system systematically produces high-PASV or low-PASV shot decisions, orthogonal to whether the system produces high or low *xPTS* per possession.

## 8.4 Broadcast and Public-Facing Analytics

The framework's per-shot signed-scalar output is well-suited to broadcast use. A real-time PASV value displayed alongside each shot in a live broadcast provides viewers a single-number decision-quality grading that is more informative than current shot-quality overlays (which typically display only the realized shot's *xPTS*). The grading distinguishes between aesthetically-impressive shots that were nonetheless off-equilibrium and aesthetically-unimpressive shots that were on-equilibrium.

Broadcast applications are conditional on tracking-data partnerships and real-time computation infrastructure. They are identified here as potential applications, not as currently-deployable products.

---

# 9. Limitations and Future Work

The PASV framework as presented in this paper carries several limitations, each of which corresponds to an identified development priority for subsequent versions of the framework.

## 9.1 Offensive-Only Formulation

The PASV v0.1 team-aggregate proxy (Section 5.1) and the per-shot PASV definition (Section 4.1) currently address only the offensive component of Possibility Cost. The defensive analog — measuring the team's ability to force the opponent into systematically low-PASV possessions — is not yet operationalized.

The defensive PASV component is identified as the highest-priority extension. The forensic analysis of Section 5.5.3 established that both pre-registered series misses in the 2026 playoff cycle are explained by the offensive-only formulation: both losing teams (Cleveland in ECF, Oklahoma City in WCF) lost to the bracket's top defensive teams. A defensive PASV component would directly address this gap.

**Proposed defensive PASV components:**
- Opponent TS% allowed (defensive analog of SDQ)
- Opponent AST% allowed (defensive analog of OPC_team)
- Opponent FTR allowed inversely (defensive analog of FFS, with sign flipped — fewer opponent FTAs implies higher defensive Possibility Cost forcing)
- Forced TOV% (defensive analog of TOV_penalty, with sign flipped)

The defensive PASV would weight in the combined v0.2 score at approximately 40–50% of the total, with the offensive PASV components retaining their existing weights normalized to the remaining 50–60%.

## 9.2 Box-Score Aggregate vs. Per-Shot Implementation

The PASV v0.1 proxy is computed from team-season box-score aggregates rather than from per-shot possession data. The full per-shot implementation of Eq. 4.1 requires continuation-value estimates *V\*(s\*)* at each shot release, which in turn require possession-tracking data with player positions, ball location, and shot-clock state at each instant.

Per-shot PASV operationalization is conditional on access to SportVU, Second Spectrum, or equivalent tracking data. The framework would benefit substantially from a data partnership with an NBA team or a league-affiliated data provider. Identification of such a partnership is identified as the highest-priority external dependency for the v0.2 release.

## 9.3 Independence Assumption in the Holding-Math Theorem

Theorem 4.1 assumes mutual independence of defender execution outcomes within and across forcing actions (Section 4.2.5). The acknowledged simplification produces a conservative estimate of cumulative mistake probability. A more rigorous formulation incorporating correlated defender outcomes — for example, via a hidden Markov coordination state across the five-defender unit — would yield higher cumulative-mistake probabilities at every *n* > 1.

The defender-coordination extension is identified as a methodological refinement for v0.2. Empirical estimation of defender-coordination correlation parameters requires possession-tracking data and is therefore conditional on the same external dependency as the per-shot PASV implementation.

## 9.4 Sovereign Exception as Conceptual Carve-Out

The Sovereign Exception (Section 7) is currently a conceptual carve-out applied qualitatively to a manually-identified set of NBA players. The framework would benefit from a quantitative Sovereign Exception identification procedure, computable from publicly-available data, that operationalizes the empirical condition of Definition 7.1.

A proposed quantitative procedure: a player qualifies for the Sovereign Exception in season *S* if and only if the player's z-scored player-specific *xPTS* on the bottom-quartile of league shot types (by mean *xPTS*) exceeds the league-average z-scored *xPTS* on the top-quartile of league shot types. The procedure is computable from publicly-available shot-by-shot data and would replace the manual identification used in Section 7.2 with an empirical screen.

## 9.5 OPC Operationalization

OPC is currently operationalized via the AST% proxy (Section 5.2). The full operationalization requires per-possession forcing-action counts, available only from tracking data. The AST% proxy systematically undercounts forcing actions that do not terminate in assists.

Full OPC operationalization is conditional on tracking-data access. The AST% proxy is sufficient for the position-stratified within-position comparisons of Section 5.3 but is not sufficient for cross-position OPC comparisons or for per-possession PASV computation.

## 9.6 Opponent Adjustment

The PASV v0.1 proxy (Section 5.1) computes each team's score from the team's own statistics without adjustment for the strength of the opponents faced. Teams playing weaker-defense schedules will exhibit artificially inflated proxy component values.

Opponent adjustment is identified as a straightforward v0.2 refinement: each component is normalized by the season-mean component value among the team's opponents, removing the schedule-strength inflation.

## 9.7 v0.2 Specification Filing

Consistent with the pre-registration discipline established by the v0.1 filing (Section 5.5), the v0.2 specification will be filed publicly prior to any predictions being made on the 2026–27 NBA season. The v0.2 specification will include defensive PASV components, the transcendent solo-star feature, the defender-coordination extension to the Holding-Math Theorem, the opponent adjustment, and the quantitative Sovereign Exception identification procedure.

---

# 10. Open-Source Release

The PASV framework is released under an open-source license consistent with the MIT Sloan Sports Analytics Conference research-paper-competition submission requirements. The release accompanies this paper at submission.

## 10.1 Repository Contents

The accompanying open-source repository (URL to be confirmed at submission) contains the following:

| File / directory | Contents |
|---|---|
| `README.md` | Project overview, installation instructions, reproduction commands |
| `LICENSE` | MIT License |
| `paper/` | Full paper PDF, abstract, supplementary appendices |
| `data/` | 2025 NBA regular-season team-aggregate CSV (basketball-reference per-game and advanced) |
| `code/pasv_v01.py` | PASV v0.1 team-aggregate computation script |
| `code/opc_proxy.py` | OPC AST% proxy computation script |
| `code/sensitivity.py` | Weight-sensitivity analysis script |
| `notebooks/validation.ipynb` | Jupyter notebook reproducing the validation results of Section 5 |
| `pre_registration/PASV_v01_PreRegistration_2026-05-26.md` | Verbatim pre-registration document, dated and hash-verified |
| `pre_registration/PASV_v01_Receipts_2026-06-03.md` | Verbatim grading document, dated post-resolution of pre-registered series |

## 10.2 Reproducibility

The full empirical validation of Section 5 is reproducible from the repository as follows:

```bash
git clone <repository_url>
cd pasv
pip install -r requirements.txt
python code/pasv_v01.py --season 2025 --output results/pasv_v01_2025.csv
jupyter notebook notebooks/validation.ipynb
```

All randomness in the validation pipeline is seeded; reproduction yields bitwise-identical numerical results to those reported in Section 5.

## 10.3 License

The repository is released under the MIT License. All authors retain ownership rights per Sloan submission policy. Users of the framework are requested (but not required) to cite the present paper in any subsequent publication or product that derives from the framework.

## 10.4 Data Provenance

All input data is sourced from basketball-reference.com per-game and advanced team-aggregate tables, 2025 NBA regular season. Data was accessed and downloaded on 2026-05-26 in conjunction with the PASV v0.1 pre-registration filing. The data files included in the repository are exact copies of the files used in the pre-registration analysis, preserving the methodology-hash discipline of the original filing.

---

# 11. References

## Primary Precursors (Basketball Analytics)

Bellotti, R. (1988). *Points Created*. Self-published.

Bleacher Report Staff. (2018, May 29). Rockets break NBA playoff record with 27 consecutive missed three-pointers. *Bleacher Report.*

Cervone, D., D'Amour, A., Bornn, L., & Goldsberry, K. (2014). A multiresolution stochastic process model for predicting basketball possession outcomes. *Journal of Quantitative Analysis in Sports*, 10(4), 305–313.

Goldsberry, K. (2012). CourtVision: New visual and spatial analytics for the NBA. *Proceedings of the 2012 MIT Sloan Sports Analytics Conference.*

Goldsberry, K. (2019). *Sprawlball: A Visual Tour of the New Era of the NBA*. Houghton Mifflin Harcourt.

Heeren, D. (1988). *Basketball Abstract*. Bobcat Books.

James, B. (1986). *The Bill James Historical Baseball Abstract*. Villard Books.

Lopez, M. J., & Matthews, G. J. (2015). Building an NCAA men's basketball predictive model and quantifying its success. *Journal of Quantitative Analysis in Sports*, 11(1), 5–12.

Manley, M. (1989). *Martin Manley's Basketball Heaven*. Doubleday.

Morey, D. (2020). Personal communication and public commentary, 2007–2020 tenure as General Manager, Houston Rockets.

Oliver, D. (2004). *Basketball on Paper: Rules and Tools for Performance Analysis*. Brassey's, Inc.

Sandholtz, N., & Bornn, L. (2018). Replaying the NBA. *Proceedings of the 2018 MIT Sloan Sports Analytics Conference.*

Skinner, B. (2012). The problem of shot selection in basketball. *PLOS ONE*, 7(1), e30776. (arXiv preprint, 2011.)

The Ringer Staff. (2018, May 29). The night the three-pointer betrayed the Rockets. *The Ringer.*

## MDP, Decision Theory, and Reinforcement Learning

Bellman, R. (1957). *Dynamic Programming*. Princeton University Press.

Browne, C. B., Powley, E., Whitehouse, D., Lucas, S. M., Cowling, P. I., Rohlfshagen, P., Tavener, S., Perez, D., Samothrakis, S., & Colton, S. (2012). A survey of Monte Carlo tree search methods. *IEEE Transactions on Computational Intelligence and AI in Games*, 4(1), 1–43.

Robbins, H. (1952). Some aspects of the sequential design of experiments. *Bulletin of the American Mathematical Society*, 58(5), 527–535.

Silver, D., Huang, A., Maddison, C. J., Guez, A., Sifre, L., van den Driessche, G., Schrittwieser, J., Antonoglou, I., Panneershelvam, V., Lanctot, M., Dieleman, S., Grewe, D., Nham, J., Kalchbrenner, N., Sutskever, I., Lillicrap, T., Leach, M., Kavukcuoglu, K., Graepel, T., & Hassabis, D. (2016). Mastering the game of Go with deep neural networks and tree search. *Nature*, 529(7587), 484–489.

Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.

## Economics and Game Theory

Bastiat, F. (1850). Ce qu'on voit et ce qu'on ne voit pas. *Journal des économistes*. (English translation: *What Is Seen and What Is Not Seen.*)

Buchanan, J. M. (1969). *Cost and Choice: An Inquiry in Economic Theory*. Markham Publishing.

Hazlitt, H. (1946). *Economics in One Lesson*. Harper & Brothers.

Jevons, W. S. (1871). *The Theory of Political Economy*. Macmillan.

Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. *Econometrica*, 47(2), 263–291.

Menger, C. (1871). *Grundsätze der Volkswirtschaftslehre*. Wilhelm Braumüller.

Nash, J. F. (1950). Non-cooperative games. Doctoral dissertation, Princeton University.

Robbins, L. (1932). *An Essay on the Nature and Significance of Economic Science*. Macmillan.

Tversky, A., & Kahneman, D. (1992). Advances in prospect theory: Cumulative representation of uncertainty. *Journal of Risk and Uncertainty*, 5(4), 297–323.

von Neumann, J. (1928). Zur Theorie der Gesellschaftsspiele. *Mathematische Annalen*, 100, 295–320.

von Neumann, J., & Morgenstern, O. (1944). *Theory of Games and Economic Behavior*. Princeton University Press.

von Wieser, F. (1914). *Theorie der gesellschaftlichen Wirtschaft*. (English translation: *Social Economics.*)

Walras, L. (1874). *Éléments d'économie politique pure*. L. Corbaz et Cie.

## Finance and Portfolio Theory

Black, F., & Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy*, 81(3), 637–654.

Kelly, J. L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926.

Markowitz, H. (1952). Portfolio selection. *Journal of Finance*, 7(1), 77–91.

Merton, R. C. (1973). Theory of rational option pricing. *Bell Journal of Economics and Management Science*, 4(1), 141–183.

## Physics and Information Theory

Feynman, R. P. (1942). The principle of least action in quantum mechanics. Doctoral dissertation, Princeton University.

Feynman, R. P. (1948). Space-time approach to non-relativistic quantum mechanics. *Reviews of Modern Physics*, 20(2), 367–387.

Kullback, S., & Leibler, R. A. (1951). On information and sufficiency. *Annals of Mathematical Statistics*, 22(1), 79–86.

Maupertuis, P. L. (1746). Les loix du mouvement et du repos déduites d'un principe métaphysique. *Histoire de l'Académie Royale des Sciences et des Belles Lettres.*

Shannon, C. E. (1948). A mathematical theory of communication. *Bell System Technical Journal*, 27(3), 379–423.

## DataDunkNBA Source Materials (Author's Prior Work)

Morong, B. (2026a). Bastiat at the free throw line. *DataDunkNBA Substack*, May 2026.

Morong, B. (2026b). Nash, Bellman, and the beautiful mind of Nikola Jokić. *DataDunkNBA Substack*, May 2026.

Morong, B. (2026c). The possibility cost of the 2018 Rockets and other variance murders. *DataDunkNBA Substack*, May 2026.

Morong, B. (2026d). PASV Finals pre-registration v0.1. *DataDunkNBA project repository*, May 26, 2026.

Morong, B. (2026e). PASV v0.1 receipts. *DataDunkNBA project repository*, June 3, 2026.

---

*Full Paper v1 complete. Sole author: Bobby Morong, DataDunkNBA. 2026-06-03.*

*Title: Every Shot Is a Measurement: A Theory of Possibility Cost in NBA Possession Value*

*Submission target: MIT Sloan Sports Analytics Conference 2027, Basketball track. Open-source repository accompanying submission.*
