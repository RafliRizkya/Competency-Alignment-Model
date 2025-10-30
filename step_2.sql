WITH employee_enriched AS (
        SELECT 
            e.employee_id,
            e.fullname,
            pos.name as position,
            dir.name AS directorate,
            g.name AS grade,
            edu.name AS education, 
            pp.disc,
            -- Kompetensi (10 TV)
            MAX(CASE WHEN cy.pillar_code = 'IDS' THEN cy.score END) AS Insight_Decision,
            MAX(CASE WHEN cy.pillar_code = 'QDD' THEN cy.score END) AS Quality_Delivery,
            MAX(CASE WHEN cy.pillar_code = 'FTC' THEN cy.score END) AS Forward_Thinking,
            MAX(CASE WHEN cy.pillar_code = 'STO' THEN cy.score END) AS Team_Orientation,
            MAX(CASE WHEN cy.pillar_code = 'CSI' THEN cy.score END) AS Commercial_Savvy,
            MAX(CASE WHEN cy.pillar_code = 'VCU' THEN cy.score END) AS Value_Creation,
            MAX(CASE WHEN cy.pillar_code = 'GDR' THEN cy.score END) AS Growth_Drive,
            MAX(CASE WHEN cy.pillar_code = 'CEX' THEN cy.score END) AS Curiosity,
            MAX(CASE WHEN cy.pillar_code = 'LIE' THEN cy.score END) AS Lead_Inspire,
            MAX(CASE WHEN cy.pillar_code = 'SEA' THEN cy.score END) AS Social_Empathy,
            
            -- Psikometri (4 TV)
            MAX(pp.pauli) AS Pauli_Score,
            MAX(pp.iq) AS IQ_Score,
            MAX(pp.gtq) AS GTQ_Score,
            MAX(pp.tiki) AS TIKI_Score,
            
            -- PAPI (2 TV)
            MAX(CASE WHEN ps.scale_code = 'Papi_P' THEN ps.score END) AS Papi_P,
            MAX(CASE WHEN ps.scale_code = 'Papi_W' THEN ps.score END) AS Papi_W
            
        FROM employees e
        LEFT JOIN dim_directorates dir ON e.directorate_id = dir.directorate_id
        LEFT JOIN dim_grades g ON e.grade_id = g.grade_id
        LEFT JOIN dim_education edu ON e.education_id = edu.education_id
        LEFT JOIN dim_positions pos ON e.position_id = pos.position_id
        LEFT JOIN profiles_psych pp ON e.employee_id = pp.employee_id
        LEFT JOIN competencies_yearly cy ON e.employee_id = cy.employee_id AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
        LEFT JOIN papi_scores ps ON e.employee_id = ps.employee_id
        GROUP BY e.employee_id, e.fullname, pos.name, dir.name, g.name, edu.name, pp.disc
    ),
    talent_structure AS (
        -- Struktur TV Baru (17 TV)
        SELECT 1 AS tv_order, 'Execution Excellence' AS tgv_name, 'Quality Delivery' AS tv_name, 'Quality_Delivery' AS column_name, 'numeric' AS data_type, 'higher_is_better' AS scoring_direction
        UNION ALL SELECT 2, 'Execution Excellence', 'Forward Thinking', 'Forward_Thinking', 'numeric', 'higher_is_better'
        UNION ALL SELECT 3, 'Execution Excellence', 'Team Orientation', 'Team_Orientation', 'numeric', 'higher_is_better'
        UNION ALL SELECT 4, 'Strategic Impact', 'Commercial Savvy', 'Commercial_Savvy', 'numeric', 'higher_is_better'
        UNION ALL SELECT 5, 'Strategic Impact', 'Value Creation', 'Value_Creation', 'numeric', 'higher_is_better'
        UNION ALL SELECT 6, 'Growth & Innovation', 'Growth Drive', 'Growth_Drive', 'numeric', 'higher_is_better'
        UNION ALL SELECT 7, 'Growth & Innovation', 'Curiosity', 'Curiosity', 'numeric', 'higher_is_better'
        UNION ALL SELECT 8, 'People Leadership', 'Lead & Inspire', 'Lead_Inspire', 'numeric', 'higher_is_better'
        UNION ALL SELECT 9, 'People Leadership', 'Social Empathy', 'Social_Empathy', 'numeric', 'higher_is_better'
        
        UNION ALL SELECT 10, 'Motivation & Drive', 'Pauli Score', 'Pauli_Score', 'numeric', 'higher_is_better'
        UNION ALL SELECT 11, 'Cognitive Complexity', 'IQ Score', 'IQ_Score', 'numeric', 'higher_is_better'
        UNION ALL SELECT 12, 'Cognitive Complexity', 'GTQ Score', 'GTQ_Score', 'numeric', 'higher_is_better'
        UNION ALL SELECT 13, 'Cognitive Complexity', 'TIKI Score', 'TIKI_Score', 'numeric', 'higher_is_better'
        
        UNION ALL SELECT 14, 'Demographics', 'Education Level', 'education', 'categorical', 'exact_match'
        UNION ALL SELECT 15, 'Demographics', 'DISC Profile', 'disc', 'categorical', 'exact_match'
        
        UNION ALL SELECT 16, 'PAPI Alignment', 'Papi_P', 'Papi_P', 'numeric', 'higher_is_better'
        UNION ALL SELECT 17, 'PAPI Alignment', 'Papi_W', 'Papi_W', 'numeric', 'higher_is_better'
    ),
    baseline_scores AS (
        SELECT tb.job_vacancy_id, tb.role_name, tb.job_level, ts.tgv_name, ts.tv_name, ts.column_name, ts.data_type, ts.scoring_direction, tb.weights_config,
            CASE 
                WHEN ts.data_type = 'categorical' THEN MODE() WITHIN GROUP (ORDER BY CASE ts.column_name 
                    WHEN 'education' THEN edu.name 
                    WHEN 'disc' THEN pp.disc 
                END)
                ELSE PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    CASE ts.column_name
                        WHEN 'Insight_Decision' THEN cy.score::NUMERIC
                        WHEN 'Quality_Delivery' THEN cy.score::NUMERIC 
                        WHEN 'Forward_Thinking' THEN cy.score::NUMERIC
                        WHEN 'Team_Orientation' THEN cy.score::NUMERIC 
                        WHEN 'Commercial_Savvy' THEN cy.score::NUMERIC
                        WHEN 'Value_Creation' THEN cy.score::NUMERIC 
                        WHEN 'Growth_Drive' THEN cy.score::NUMERIC
                        WHEN 'Curiosity' THEN cy.score::NUMERIC 
                        WHEN 'Lead_Inspire' THEN cy.score::NUMERIC 
                        WHEN 'Social_Empathy' THEN cy.score::NUMERIC
                        WHEN 'Pauli_Score' THEN pp.pauli::NUMERIC
                        WHEN 'IQ_Score' THEN pp.iq::NUMERIC
                        WHEN 'GTQ_Score' THEN pp.gtq::NUMERIC
                        WHEN 'TIKI_Score' THEN pp.tiki::NUMERIC
                        WHEN 'Papi_P' THEN ps.score::NUMERIC
                        WHEN 'Papi_W' THEN ps.score::NUMERIC
                    END
                )::TEXT
            END AS baseline_score
        FROM talent_benchmarks tb
        CROSS JOIN talent_structure ts
        INNER JOIN UNNEST(tb.selected_talent_ids) AS benchmark_employee_id ON TRUE
        INNER JOIN employees e ON e.employee_id = benchmark_employee_id
        LEFT JOIN dim_education edu ON e.education_id = edu.education_id
        LEFT JOIN profiles_psych pp ON e.employee_id = pp.employee_id
        LEFT JOIN competencies_yearly cy ON e.employee_id = cy.employee_id AND cy.year = (SELECT MAX(year) FROM competencies_yearly)
        LEFT JOIN papi_scores ps ON e.employee_id = ps.employee_id
        GROUP BY tb.job_vacancy_id, tb.role_name, tb.job_level, ts.tgv_name, ts.tv_name, ts.column_name, ts.data_type, ts.scoring_direction, tb.weights_config
        
        -- KOREKSI: MENGEMBALIKAN LOGIKA LENGKAP UNTUK MENGHINDARI '...'
        HAVING CASE 
            WHEN ts.data_type = 'categorical' THEN 
                MODE() WITHIN GROUP (ORDER BY CASE ts.column_name WHEN 'education' THEN edu.name WHEN 'disc' THEN pp.disc END) IS NOT NULL
            ELSE 
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    CASE ts.column_name
                        WHEN 'Insight_Decision' THEN cy.score::NUMERIC
                        WHEN 'Quality_Delivery' THEN cy.score::NUMERIC 
                        WHEN 'Forward_Thinking' THEN cy.score::NUMERIC
                        WHEN 'Team_Orientation' THEN cy.score::NUMERIC 
                        WHEN 'Commercial_Savvy' THEN cy.score::NUMERIC
                        WHEN 'Value_Creation' THEN cy.score::NUMERIC 
                        WHEN 'Growth_Drive' THEN cy.score::NUMERIC
                        WHEN 'Curiosity' THEN cy.score::NUMERIC 
                        WHEN 'Lead_Inspire' THEN cy.score::NUMERIC 
                        WHEN 'Social_Empathy' THEN cy.score::NUMERIC
                        WHEN 'Pauli_Score' THEN pp.pauli::NUMERIC
                        WHEN 'IQ_Score' THEN pp.iq::NUMERIC
                        WHEN 'GTQ_Score' THEN pp.gtq::NUMERIC
                        WHEN 'TIKI_Score' THEN pp.tiki::NUMERIC
                        WHEN 'Papi_P' THEN ps.score::NUMERIC
                        WHEN 'Papi_W' THEN ps.score::NUMERIC
                    END
                )::TEXT IS NOT NULL
        END
    ),
    tv_match_rates AS (
        SELECT e.employee_id, e.directorate, e.grade, e.position,
            bs.job_vacancy_id, bs.job_level, bs.tgv_name, bs.tv_name, bs.baseline_score, bs.role_name, bs.weights_config,
            
            -- Ambil user_score
            CASE bs.column_name
                WHEN 'Insight_Decision' THEN e.Insight_Decision::TEXT 
                WHEN 'Quality_Delivery' THEN e.Quality_Delivery::TEXT
                WHEN 'Forward_Thinking' THEN e.Forward_Thinking::TEXT 
                WHEN 'Team_Orientation' THEN e.Team_Orientation::TEXT
                WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy::TEXT 
                WHEN 'Value_Creation' THEN e.Value_Creation::TEXT
                WHEN 'Growth_Drive' THEN e.Growth_Drive::TEXT 
                WHEN 'Curiosity' THEN e.Curiosity::TEXT
                WHEN 'Lead_Inspire' THEN e.Lead_Inspire::TEXT 
                WHEN 'Social_Empathy' THEN e.Social_Empathy::TEXT 
                WHEN 'Pauli_Score' THEN e.Pauli_Score::TEXT
                WHEN 'IQ_Score' THEN e.IQ_Score::TEXT
                WHEN 'GTQ_Score' THEN e.GTQ_Score::TEXT
                WHEN 'TIKI_Score' THEN e.TIKI_Score::TEXT
                WHEN 'Papi_P' THEN e.Papi_P::TEXT
                WHEN 'Papi_W' THEN e.Papi_W::TEXT
                WHEN 'education' THEN e.education 
                WHEN 'disc' THEN e.disc
            END AS user_score,
            
            -- Hitung tv_match_rate
            CASE 
                WHEN bs.data_type = 'categorical' THEN
                    CASE 
                        WHEN bs.tv_name = 'Education Level' THEN
                            -- LOGIKA BERJENJANG KHUSUS UNTUK PENDIDIKAN (D3 < S1 < S2)
                            CASE 
                                WHEN (CASE e.education WHEN 'D3' THEN 3 WHEN 'S1' THEN 4 WHEN 'S2' THEN 5 ELSE 0 END) >= 
                                    (CASE bs.baseline_score WHEN 'D3' THEN 3 WHEN 'S1' THEN 4 WHEN 'S2' THEN 5 ELSE 0 END)
                                THEN 100.00 
                                ELSE 0.00 
                            END
                        -- Jika bukan Education Level, cek exact match dan NULL
                        WHEN (CASE bs.column_name WHEN 'education' THEN e.education WHEN 'disc' THEN e.disc END) IS NULL THEN NULL
                        WHEN (CASE bs.column_name WHEN 'education' THEN e.education WHEN 'disc' THEN e.disc END) = bs.baseline_score THEN 100.00 
                        ELSE 0.00 
                    END
                WHEN bs.scoring_direction = 'higher_is_better' THEN
                    -- Logika Higher Is Better untuk semua 15 skor numerik
                    CASE 
                        WHEN bs.baseline_score IS NULL OR bs.baseline_score::NUMERIC = 0 THEN NULL
                        WHEN (CASE bs.column_name 
                            WHEN 'Insight_Decision' THEN e.Insight_Decision 
                            WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                            WHEN 'Forward_Thinking' THEN e.Forward_Thinking 
                            WHEN 'Team_Orientation' THEN e.Team_Orientation 
                            WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy 
                            WHEN 'Value_Creation' THEN e.Value_Creation 
                            WHEN 'Growth_Drive' THEN e.Growth_Drive 
                            WHEN 'Curiosity' THEN e.Curiosity 
                            WHEN 'Lead_Inspire' THEN e.Lead_Inspire 
                            WHEN 'Social_Empathy' THEN e.Social_Empathy 
                            WHEN 'Pauli_Score' THEN e.Pauli_Score
                            WHEN 'IQ_Score' THEN e.IQ_Score
                            WHEN 'GTQ_Score' THEN e.GTQ_Score
                            WHEN 'TIKI_Score' THEN e.TIKI_Score
                            WHEN 'Papi_P' THEN e.Papi_P 
                            WHEN 'Papi_W' THEN e.Papi_W
                        END)::NUMERIC IS NULL THEN NULL
                        ELSE LEAST(((CASE bs.column_name 
                            WHEN 'Insight_Decision' THEN e.Insight_Decision 
                            WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                            WHEN 'Forward_Thinking' THEN e.Forward_Thinking 
                            WHEN 'Team_Orientation' THEN e.Team_Orientation 
                            WHEN 'Commercial_Savvy' THEN e.Commercial_Savvy 
                            WHEN 'Value_Creation' THEN e.Value_Creation 
                            WHEN 'Growth_Drive' THEN e.Growth_Drive 
                            WHEN 'Curiosity' THEN e.Curiosity 
                            WHEN 'Lead_Inspire' THEN e.Lead_Inspire 
                            WHEN 'Social_Empathy' THEN e.Social_Empathy 
                            WHEN 'Pauli_Score' THEN e.Pauli_Score
                            WHEN 'IQ_Score' THEN e.IQ_Score
                            WHEN 'GTQ_Score' THEN e.GTQ_Score
                            WHEN 'TIKI_Score' THEN e.TIKI_Score
                            WHEN 'Papi_P' THEN e.Papi_P 
                            WHEN 'Papi_W' THEN e.Papi_W
                        END)::NUMERIC / bs.baseline_score::NUMERIC) * 100, 100.00) 
                    END
                -- Logika Lower Is Better (dipertahankan untuk keamanan, meskipun saat ini tidak digunakan)
                WHEN bs.scoring_direction = 'lower_is_better' THEN
                    CASE 
                        WHEN bs.baseline_score IS NULL OR bs.baseline_score::NUMERIC = 0 THEN NULL
                        WHEN (CASE bs.column_name 
                            WHEN 'Insight_Decision' THEN e.Insight_Decision 
                            WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                            -- Tambahkan semua kolom Lower Is Better di sini
                            ELSE NULL 
                        END)::NUMERIC IS NULL THEN NULL
                        ELSE LEAST(((2 * bs.baseline_score::NUMERIC - (CASE bs.column_name 
                            WHEN 'Insight_Decision' THEN e.Insight_Decision 
                            WHEN 'Quality_Delivery' THEN e.Quality_Delivery 
                            -- Tambahkan semua kolom Lower Is Better di sini
                            ELSE NULL
                        END)::NUMERIC) / bs.baseline_score::NUMERIC) * 100, 100.00) 
                    END
                ELSE NULL
            END AS tv_match_rate
        FROM employee_enriched e 
        INNER JOIN baseline_scores bs 
            ON bs.role_name = e.position 
            AND bs.job_level = e.grade
    ),
    tgv_match_rates AS (
        SELECT employee_id, job_vacancy_id, tgv_name, weights_config,
            ROUND(AVG(tv_match_rate), 2) AS tgv_match_rate
        FROM tv_match_rates
        WHERE tv_match_rate IS NOT NULL
        GROUP BY employee_id, job_vacancy_id, tgv_name, weights_config
    ),
    final_match_rates AS (
        SELECT tgv.employee_id, tgv.job_vacancy_id,
            ROUND(
                CASE 
                    WHEN tgv.weights_config ? 'tgv_weights' THEN
                        SUM(tgv.tgv_match_rate * COALESCE(
                            CASE tgv.tgv_name
                                WHEN 'PAPI Alignment' THEN (tgv.weights_config->'tgv_weights'->>'Motivation & Drive')::NUMERIC
                                WHEN 'People Leadership' THEN (tgv.weights_config->'tgv_weights'->>'Leadership & Influence')::NUMERIC
                                WHEN 'Execution Excellence' THEN (tgv.weights_config->'tgv_weights'->>'Conscientiousness & Reliability')::NUMERIC
                                WHEN 'Strategic Impact' THEN (tgv.weights_config->'tgv_weights'->>'Social Orientation & Collaboration')::NUMERIC
                                WHEN 'Growth & Innovation' THEN (tgv.weights_config->'tgv_weights'->>'Creativity & Innovation Orientation')::NUMERIC
                                WHEN 'Demographics' THEN (tgv.weights_config->'tgv_weights'->>'Cognitive Complexity & Problem-Solving')::NUMERIC
                                WHEN 'Motivation & Drive' THEN (tgv.weights_config->'tgv_weights'->>'Motivation & Drive')::NUMERIC 
                                WHEN 'Cognitive Complexity' THEN (tgv.weights_config->'tgv_weights'->>'Cognitive Complexity & Problem-Solving')::NUMERIC
                                ELSE 0
                            END, 0
                        )) / NULLIF(
                            SUM(COALESCE(
                                CASE tgv.tgv_name
                                    WHEN 'PAPI Alignment' THEN (tgv.weights_config->'tgv_weights'->>'Motivation & Drive')::NUMERIC
                                    WHEN 'People Leadership' THEN (tgv.weights_config->'tgv_weights'->>'Leadership & Influence')::NUMERIC
                                    WHEN 'Execution Excellence' THEN (tgv.weights_config->'tgv_weights'->>'Conscientiousness & Reliability')::NUMERIC
                                    WHEN 'Strategic Impact' THEN (tgv.weights_config->'tgv_weights'->>'Social Orientation & Collaboration')::NUMERIC
                                    WHEN 'Growth & Innovation' THEN (tgv.weights_config->'tgv_weights'->>'Creativity & Innovation Orientation')::NUMERIC
                                    WHEN 'Demographics' THEN (tgv.weights_config->'tgv_weights'->>'Cognitive Complexity & Problem-Solving')::NUMERIC
                                    WHEN 'Motivation & Drive' THEN (tgv.weights_config->'tgv_weights'->>'Motivation & Drive')::NUMERIC
                                    WHEN 'Cognitive Complexity' THEN (tgv.weights_config->'tgv_weights'->>'Cognitive Complexity & Problem-Solving')::NUMERIC
                                    ELSE 0
                                END, 0
                            )), 0
                        )
                    ELSE 
                        AVG(tgv.tgv_match_rate) 
                END, 2
            ) AS final_match_rate
        FROM tgv_match_rates tgv
        GROUP BY tgv.employee_id, tgv.job_vacancy_id, tgv.weights_config
    )
    SELECT
        tv.employee_id,
        tv.directorate,
        tv.role_name AS role,
        tv.grade,
        tv.tgv_name,
        tv.tv_name,
        tv.baseline_score,
        tv.user_score,
        ROUND(tv.tv_match_rate, 2) AS tv_match_rate,
        tgv.tgv_match_rate,
        fm.final_match_rate
    FROM tv_match_rates tv
    INNER JOIN tgv_match_rates tgv 
        ON tv.employee_id = tgv.employee_id 
        AND tv.job_vacancy_id = tgv.job_vacancy_id 
        AND tv.tgv_name = tgv.tgv_name
    INNER JOIN final_match_rates fm 
        ON tv.employee_id = fm.employee_id 
        AND tv.job_vacancy_id = fm.job_vacancy_id
    WHERE tv.tv_match_rate IS NOT NULL
    ORDER BY fm.final_match_rate DESC, tv.tgv_name, tv.tv_name;