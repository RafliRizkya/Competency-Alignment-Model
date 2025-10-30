CREATE OR REPLACE VIEW employee_report AS
WITH strengths_agg AS (
  SELECT
    employee_id,
    STRING_AGG(theme, ', ') AS employee_strengths
  FROM 
    strengths
  GROUP BY 
    employee_id
),
papi_agg AS (
  SELECT
    employee_id,
    JSON_AGG(
      JSON_BUILD_OBJECT(
        'scale_code', scale_code,
        'score', score
      )
    ) AS papi_data
  FROM 
    papi_scores
  GROUP 
    BY employee_id
),
education_cte AS (
  SELECT
    e.employee_id,
    CONCAT_WS(' - ', de.name, dm.name) AS education
  FROM 
    employees e
  LEFT JOIN 
    dim_education de 
  ON 
    e.education_id = de.education_id
  LEFT JOIN
     dim_majors dm 
  ON 
    e.major_id = dm.major_id
),
competencies_cte AS (
  SELECT
    cy.employee_id,
    JSON_AGG(
  JSON_BUILD_OBJECT(
    'scale_code', cp.pillar_code,
    'score', cy.score
  )
  ) AS competencies
  FROM 
    competencies_yearly cy
  LEFT JOIN 
    dim_competency_pillars cp
  ON 
    cp.pillar_code = cy.pillar_code
  GROUP BY 
    cy.employee_id
),
profiles_cte AS (
  SELECT
    employee_id,
    disc,
    disc_word,
    mbti,
    iq,
    gtq
  FROM 
    profiles_psych
)
SELECT
  e.employee_id,
  e.fullname AS full_name,
  e.years_of_service_months AS work_duration_months,
  edu.education,
  p.disc,
  p.disc_word,
  p.mbti,
  p.iq,
  p.gtq,
  pa.papi_data,
  sa.employee_strengths,
  cc.competencies,
  py.rating,
  py.year
FROM 
  employees e
LEFT JOIN 
  competencies_cte cc 
ON 
  cc.employee_id = e.employee_id
LEFT JOIN 
  papi_agg pa
ON 
  pa.employee_id = e.employee_id
LEFT JOIN
  strengths_agg sa 
ON 
sa.employee_id = e.employee_id
LEFT JOIN 
  education_cte edu 
ON 
  edu.employee_id = e.employee_id
LEFT JOIN 
  profiles_cte p 
ON 
  p.employee_id = e.employee_id
LEFT JOIN 
  performance_yearly py 
ON 
  py.employee_id = e.employee_id
ORDER BY 
  py.year ASC, 
  py.rating DESC