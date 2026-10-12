# How the Student Success Score works

The score is a number from 0 to 100 built from seven indicators. Each one is first
turned into a 0 to 100 component score, then the components are combined with fixed weights.

| Component | How it's calculated | Weight (yr 3-4) | Weight (yr 2) |
|---|---|---|---|
| Academics | 75% from CGPA (x10), 25% from backlogs (each active backlog costs 25, max 4) | 25% | 30% |
| Attendance | Overall attendance % across all subjects this semester | 15% | 20% |
| LMS activity | 35% login frequency (5 a week = full marks), 65% share of assignments submitted | 15% | 15% |
| Placement readiness | Average of aptitude, coding and mock interview scores; a test not taken counts as 0 | 20% | 5% |
| Skills | 60% technical assessment, 40% soft-skill assessment | 10% | 10% |
| Engagement | Clubs x12 + events x6 + hackathons x15 + certifications x12, capped at 100 | 10% | 15% |
| Feedback | Half student satisfaction, half faculty rating, both rescaled from 1-5 | 5% | 5% |

**Why the weights look like this.** Academics and attendance are what decide whether a
student finishes the degree, so together they carry 40% (50% for second years).
Placement readiness gets 20% for third and fourth years because that's when it matters;
second years haven't started placement prep, so penalising them for it would be unfair.
Feedback is only 5% because it's self-reported and noisy, but it's often the first sign
that a student is unhappy, so we didn't want to drop it completely.

**How we explain it.** Because the score is a weighted sum, the gap between a student
and their year's average splits exactly into one piece per component:

    score - year average = sum of  weight x (component - year average for that component)

So for every student we can say, for example, "8 points below average: 5 lost on
placement readiness, 2 on attendance, 1 on engagement". That's the "Why this score"
chart on each student's page.

**Risk is separate from the score.** The score describes where a student is today.
The two risk models estimate where they're heading. They're logistic regressions trained
on last year's batch: one predicts serious academic trouble (CGPA, backlogs, attendance,
assignment completion, LMS logins), the other predicts finishing without a placement
(CGPA, backlogs, aptitude, coding, mock interview, skills, certifications, hackathons).
On a held-out 25% of that data they score an AUC of about 0.83 and 0.80. For each
student we show which indicators push their risk up the most.

A student is marked **High risk** if any serious flag is raised (attendance under 65%,
3+ backlogs, or either model above 55%), **Medium** if a model is above 30%, there are
two or more smaller flags, or the score is under 50, and **Low** otherwise.

**Segments** group students who need the same kind of help (for example "strong
academics, low placement readiness"), each with a suggested action, so a placement
officer or HOD can act on a group instead of one student at a time.
