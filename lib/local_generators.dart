/// Local, deterministic generators for CareerLens AI.
/// These generators use only form input; they require no network or AI API.

List<String> _localSkills(String text) {
  const patterns = <String, String>{
    'Python': r'\bpython\b',
    'Java': r'\bjava\b',
    'JavaScript': r'\bjavascript\b',
    'TypeScript': r'\btypescript\b',
    'SQL': r'\bsql\b',
    'MySQL': r'\bmysql\b',
    'PostgreSQL': r'\bpostgres(?:ql)?\b',
    'HTML': r'\bhtml\b',
    'CSS': r'\bcss\b',
    'React': r'\breact\b',
    'Node.js': r'\bnode(?:\.js)?\b',
    'Flask': r'\bflask\b',
    'Django': r'\bdjango\b',
    'REST APIs': r'\brest(?:ful)?\s+apis?\b|\bapi development\b',
    'Git': r'\bgit\b',
    'GitHub': r'\bgithub\b',
    'Linux': r'\blinux\b',
    'AWS': r'\baws\b|amazon web services',
    'Docker': r'\bdocker\b',
    'Kubernetes': r'\bkubernetes\b|\bk8s\b',
    'Machine Learning': r'\bmachine[\s-]+learning\b',
    'Deep Learning': r'\bdeep[\s-]+learning\b',
    'NLP': r'\bnlp\b|natural language processing',
    'TensorFlow': r'\btensorflow\b',
    'PyTorch': r'\bpytorch\b',
    'Pandas': r'\bpandas\b',
    'NumPy': r'\bnumpy\b',
    'Scikit-learn': r'\bscikit[\s-]?learn\b|\bsklearn\b',
    'Statistics': r'\bstatistics?\b',
    'Data Analysis': r'\bdata analysis\b',
    'Excel': r'\bexcel\b',
    'Power BI': r'\bpower\s*bi\b',
    'Tableau': r'\btableau\b',
    'Data Structures and Algorithms': r'\bdata structures\b|\balgorithms\b|\bdsa\b',
    'System Design': r'\bsystem design\b',
    'Cybersecurity': r'\bcyber[\s-]?security\b',
    'Networking': r'\bnetworking\b|\btcp/ip\b',
    'Flutter': r'\bflutter\b',
    'Dart': r'\bdart\b',
    'Testing': r'\btesting\b|\bunit tests?\b|\bautomated tests?\b',
  };
  return patterns.entries
      .where((entry) => RegExp(entry.value, caseSensitive: false).hasMatch(text))
      .map((entry) => entry.key)
      .toList();
}

List<String> _localRoleSkills(String role) {
  final value = role.toLowerCase();
  if (value.contains('machine learning') ||
      value.contains('ml engineer') ||
      value.contains('artificial intelligence') ||
      value.contains('ai engineer')) {
    return ['Python', 'SQL', 'Statistics', 'Pandas', 'NumPy',
      'Machine Learning', 'Scikit-learn', 'PyTorch', 'Git', 'REST APIs'];
  }
  if (value.contains('data scientist') || value.contains('data science')) {
    return ['Python', 'SQL', 'Statistics', 'Pandas', 'NumPy',
      'Data Analysis', 'Machine Learning', 'Scikit-learn'];
  }
  if (value.contains('data analyst')) {
    return ['SQL', 'Excel', 'Statistics', 'Data Analysis', 'Power BI', 'Tableau', 'Python'];
  }
  if (value.contains('frontend') || value.contains('front-end') || value.contains('web developer')) {
    return ['HTML', 'CSS', 'JavaScript', 'React', 'Git', 'Testing'];
  }
  if (value.contains('full stack') || value.contains('full-stack')) {
    return ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js', 'SQL', 'REST APIs', 'Git'];
  }
  if (value.contains('backend') || value.contains('back-end')) {
    return ['Python', 'Java', 'SQL', 'REST APIs', 'Git', 'Testing', 'Docker'];
  }
  if (value.contains('devops') || value.contains('cloud engineer')) {
    return ['Linux', 'Networking', 'Git', 'AWS', 'Docker', 'Kubernetes'];
  }
  if (value.contains('cybersecurity') || value.contains('security analyst')) {
    return ['Networking', 'Linux', 'Cybersecurity', 'Testing', 'Python'];
  }
  if (value.contains('flutter') || value.contains('mobile developer') || value.contains('android developer')) {
    return ['Flutter', 'Dart', 'Java', 'REST APIs', 'Git', 'Testing', 'SQL'];
  }
  return ['Data Structures and Algorithms', 'Java', 'Python', 'SQL', 'Git', 'Testing', 'REST APIs'];
}

String _localRoleLabel(String text) {
  final value = text.toLowerCase();
  if (value.contains('machine learning engineer') || value.contains('ml engineer') || value.contains('ai engineer')) return 'Machine Learning Engineer';
  if (value.contains('data scientist') || value.contains('data science')) return 'Data Scientist';
  if (value.contains('data analyst')) return 'Data Analyst';
  if (value.contains('software engineer') || value.contains('software developer')) return 'Software Engineer';
  if (value.contains('frontend') || value.contains('front-end')) return 'Frontend Developer';
  if (value.contains('full stack') || value.contains('full-stack')) return 'Full Stack Developer';
  if (value.contains('backend') || value.contains('back-end')) return 'Backend Developer';
  if (value.contains('devops') || value.contains('cloud engineer')) return 'Cloud / DevOps Engineer';
  if (value.contains('cybersecurity') || value.contains('security analyst')) return 'Cybersecurity Analyst';
  if (value.contains('flutter developer') || value.contains('mobile developer')) return 'Mobile App Developer';
  final lines = text.split(RegExp(r'[\r\n]+')).map((line) => line.trim()).where((line) => line.isNotEmpty).toList();
  if (lines.isNotEmpty && lines.first.length < 80) return lines.first;
  return 'the advertised role';
}

String _localResource(String skill) {
  const urls = <String, String>{
    'Python': 'https://docs.python.org/3/tutorial/',
    'Java': 'https://dev.java/learn/',
    'JavaScript': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide',
    'TypeScript': 'https://www.typescriptlang.org/docs/',
    'SQL': 'https://sqlbolt.com/',
    'HTML': 'https://developer.mozilla.org/en-US/docs/Learn/HTML',
    'CSS': 'https://developer.mozilla.org/en-US/docs/Learn/CSS',
    'React': 'https://react.dev/learn',
    'Node.js': 'https://nodejs.org/en/learn',
    'Git': 'https://git-scm.com/book/en/v2',
    'AWS': 'https://skillbuilder.aws/',
    'Docker': 'https://docs.docker.com/get-started/',
    'Kubernetes': 'https://kubernetes.io/docs/tutorials/kubernetes-basics/',
    'Machine Learning': 'https://developers.google.com/machine-learning/crash-course',
    'Pandas': 'https://pandas.pydata.org/docs/getting_started/',
    'NumPy': 'https://numpy.org/learn/',
    'Scikit-learn': 'https://scikit-learn.org/stable/tutorial/',
    'PyTorch': 'https://pytorch.org/tutorials/',
    'Statistics': 'https://www.khanacademy.org/math/statistics-probability',
    'Data Structures and Algorithms': 'https://visualgo.net/en',
    'Flutter': 'https://docs.flutter.dev/',
    'Dart': 'https://dart.dev/language',
    'Cybersecurity': 'https://tryhackme.com/',
    'Networking': 'https://skillsforall.com/',
    'Excel': 'https://support.microsoft.com/excel',
    'Power BI': 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi',
    'Tableau': 'https://www.tableau.com/learn/training',
  };
  return urls[skill] ?? 'https://www.freecodecamp.org/learn/';
}

Map<String, dynamic> generateLocalTool(String toolId, Map<String, dynamic> data) {
  final resume = (data['resume_text'] ?? '').toString().trim();
  final jd = (data['job_description'] ?? '').toString().trim();
  final internship = (data['internship_description'] ?? '').toString().trim();
  final target = (data['target_role'] ?? '').toString().trim();
  final roleText = internship.isNotEmpty ? internship : jd;
  final resumeSkills = _localSkills(resume);
  final jdSkills = _localSkills(roleText);
  final requiredSkills = jdSkills.isNotEmpty ? jdSkills : _localRoleSkills(roleText);
  final matched = requiredSkills.where(resumeSkills.contains).toList();
  final missing = requiredSkills.where((skill) => !resumeSkills.contains(skill)).toList();

  if (toolId == 'cover') {
    final suppliedName = (data['user_name'] ?? '').toString().trim();
    final name = suppliedName.isEmpty ? 'Applicant' : suppliedName;
    final role = _localRoleLabel(jd);
    final evidenceSkills = matched.isNotEmpty ? matched : resumeSkills;
    final evidence = evidenceSkills.isEmpty
        ? 'I am motivated to learn, solve problems and collaborate with your team.'
        : 'My current skills include ' + evidenceSkills.take(5).join(', ') +
            ', and I am keen to apply them while continuing to learn.';
    final letter = 'Dear Hiring Manager,\n\n'
        'I am writing to apply for the ' + role + ' position. I am interested in contributing to your team and developing practical, role-relevant skills.\n\n'
        + evidence + ' I value clear communication, thoughtful problem-solving and being honest about the work I have completed and the areas I am continuing to learn.\n\n'
        'I would welcome the opportunity to discuss how my background and projects align with your needs. Thank you for considering my application.\n\n'
        'Sincerely,\n' + name;
    return {'cover_letter': letter, 'word_count': letter.split(RegExp(r'\s+')).length, 'language': 'en'};
  }

  if (toolId == 'ats') {
    if (resume.isEmpty) throw Exception('Paste or upload your resume text to run ATS analysis.');
    final keywordScore = requiredSkills.isEmpty ? 45 : (matched.length * 100 / requiredSkills.length).round();
    final qualityScore = resume.split(RegExp(r'\s+')).length >= 80 ? 75 : 55;
    final score = (keywordScore * 0.8 + qualityScore * 0.2).round().clamp(0, 100);
    return {
      'ats_score': score,
      'score_breakdown': {'keyword_match': keywordScore, 'skills_coverage': keywordScore, 'experience_relevance': 50, 'education_match': 60, 'resume_quality': qualityScore},
      'matched_skills': matched,
      'missing_keywords': missing,
      'weak_skills': missing.take(5).toList(),
      'role_fit_summary': 'Local comparison found ' + matched.length.toString() + ' matching skill(s) and ' + missing.length.toString() + ' potential gap(s). Keyword matching cannot judge skill depth.',
      'top_strengths': matched.map((skill) => 'Resume text includes ' + skill + '.').toList(),
      'improvement_actions': missing.take(5).map((skill) => 'Practise ' + skill + ' and add a project only if you can demonstrate it.').toList(),
      'overall_verdict': score >= 80 ? 'Strong keyword alignment' : score >= 55 ? 'Some alignment — review the gaps' : 'Several potential gaps to review',
    };
  }

  if (toolId == 'skills') {
    if (jd.isEmpty) throw Exception('Enter a job description to analyse skills.');
    final gaps = missing.take(10).toList().asMap().entries.map((entry) {
      final skill = entry.value;
      return <String, dynamic>{
        'skill': skill,
        'importance': entry.key < 3 ? 'high' : 'medium',
        'reason': 'Mentioned in the job description but not detected in the supplied resume text.',
        'learning_time': ['Machine Learning', 'Deep Learning', 'Kubernetes', 'System Design'].contains(skill) ? '3–6 weeks' : '1–4 weeks',
        'free_resources': [{'name': 'Free learning resource for ' + skill, 'url': _localResource(skill), 'type': 'official/free learning'}],
      };
    }).toList();
    final plan = (missing.isNotEmpty ? missing : requiredSkills).take(4).toList();
    final roadmap = plan.asMap().entries.map((entry) => <String, dynamic>{
      'week': entry.key + 1,
      'focus': 'Learn and practise ' + entry.value,
      'resources': [entry.value + ': ' + _localResource(entry.value)],
      'milestone': 'Complete a small exercise demonstrating ' + entry.value + '.',
    }).toList();
    return {
      'critical_gaps': gaps,
      'nice_to_have_gaps': [],
      'learning_roadmap': roadmap,
      'quick_wins': [
        if (missing.isNotEmpty) 'Practise ' + missing.first + ' with a small project.' else 'Keep your resume aligned with role requirements.',
        'Describe what you personally built, tested or analysed.',
        'Only list skills you can demonstrate.',
      ],
      'career_advice': 'Detected ' + matched.length.toString() + ' matching skill(s) and ' + missing.length.toString() + ' potential gap(s). A missing keyword does not necessarily mean you lack a skill.',
      'matched_skills': matched,
    };
  }

  if (toolId == 'roadmap') {
    if (target.isEmpty) throw Exception('Enter your target role.');
    final skills = _localRoleSkills(target);
    final gaps = skills.where((skill) => !resumeSkills.contains(skill)).toList();
    final plan = (gaps + skills.where(resumeSkills.contains)).take(8).toList();
    List<String> phase(int start, int end) => plan.skip(start).take(end - start).toList();
    final project = target.toLowerCase().contains('data')
        ? 'Analyse a public dataset, explain findings with charts and document limitations.'
        : target.toLowerCase().contains('machine') || target.toLowerCase().contains('ai')
            ? 'Build an end-to-end machine-learning project with preparation, evaluation and a demo.'
            : 'Build a small tested project that demonstrates the target role skills.';
    return {
      'current_level': resumeSkills.isEmpty ? 'Not enough resume text to detect current skills' : 'Detected skills: ' + resumeSkills.take(5).join(', '),
      'target_level': 'Entry-level readiness for ' + target,
      'estimated_timeline': '12 weeks at a consistent study pace',
      'roadmap_phases': [
        {'phase': 'Phase 1: Build the foundations', 'duration': 'Weeks 1–4', 'goals': ['Learn core concepts and practise consistently.', 'Complete small exercises.'], 'skills_to_build': phase(0, 3), 'certifications': [], 'projects_to_build': ['Complete exercises and document what you learned.'], 'milestone': 'Explain the concepts and demonstrate them in a small example.'},
        {'phase': 'Phase 2: Apply the skills', 'duration': 'Weeks 5–8', 'goals': ['Combine skills in a realistic task.', 'Add tests and documentation.'], 'skills_to_build': phase(3, 6), 'certifications': [], 'projects_to_build': [project], 'milestone': 'Publish a working project with a README and demo.'},
        {'phase': 'Phase 3: Prepare for applications', 'duration': 'Weeks 9–12', 'goals': ['Practise role-specific questions.', 'Refine your resume using project evidence.'], 'skills_to_build': phase(6, 8), 'certifications': [], 'projects_to_build': ['Polish your strongest project and prepare a two-minute explanation.'], 'milestone': 'Have a role-focused resume and demonstrable project ready.'},
      ],
      'internship_opportunities': [{'type': target + ' internship or entry-level role', 'companies_to_target': [], 'how_to_apply': 'Use official company career pages and verify eligibility and deadlines.'}],
      'networking_strategy': ['Keep GitHub projects clear with setup steps and honest descriptions.', 'Ask a mentor or peer to review one project.', 'Track applications and follow up politely.'],
      'salary_range': {},
      'motivational_note': 'Adjust the pace to your study workload and mark a skill as mastered only when you can demonstrate it.',
    };
  }

  if (toolId == 'interview') {
    if (jd.isEmpty) throw Exception('Enter a job description to generate interview questions.');
    final skills = (jdSkills.isNotEmpty ? jdSkills : _localRoleSkills(jd)).take(6).toList();
    final technical = skills.map((skill) => <String, dynamic>{
      'question': 'Explain a project or exercise where you used ' + skill + '. What did you do and how did you test it?',
      'expected_answer_points': ['Explain the purpose of ' + skill + '.', 'Describe your own steps and decisions.', 'Explain how you tested the result and what you learned.'],
      'difficulty': 'beginner',
    }).toList();
    final firstSkill = skills.isEmpty ? 'your technical skills' : skills.first;
    return {
      'behavioral_questions': [
        {'question': 'Tell me about a time you had to learn something unfamiliar to finish a task.', 'why_asked': 'Assesses adaptability.', 'sample_answer_framework': 'Use STAR: situation, task, actions you took, and the truthful result.', 'tip': 'Choose a real college, project or work example.'},
        {'question': 'Describe a problem you found in a project. How did you respond?', 'why_asked': 'Assesses ownership.', 'sample_answer_framework': 'Explain the issue, investigation, fix and lesson.', 'tip': 'Do not invent outcomes.'},
      ],
      'technical_questions': technical,
      'situational_questions': [{'question': 'If a task involving ' + firstSkill + ' failed before a deadline, how would you investigate it?', 'ideal_approach': 'Reproduce the issue, inspect inputs, isolate the cause, test a fix and communicate status.'}],
      'questions_to_ask_interviewer': ['What would a successful first month look like?', 'Which tools does the team use most?', 'How are code reviews and learning supported?'],
      'preparation_checklist': ['Review ' + skills.take(4).join(', ') + '.', 'Prepare two real project examples.', 'Practise explaining decisions, tests and lessons learned.'],
    };
  }

  if (toolId == 'internship') {
    if (internship.isEmpty) throw Exception('Enter an internship description.');
    final needed = jdSkills.isNotEmpty ? jdSkills : _localRoleSkills(internship);
    final found = needed.where(resumeSkills.contains).toList();
    final missingSkills = needed.where((skill) => !resumeSkills.contains(skill)).toList();
    final hasProject = resume.toLowerCase().contains('project');
    final hasStudent = resume.toLowerCase().contains('student');
    final score = needed.isEmpty ? (resume.isEmpty ? 35 : 55) : (found.length * 70 / needed.length + (hasProject ? 15 : 0) + (hasStudent ? 5 : 0)).round().clamp(0, 100);
    return {
      'internship_fit_score': score,
      'should_apply': score >= 50,
      'matched_skills': found,
      'missing_skills': missingSkills,
      'has_projects': hasProject,
      'has_prior_internship': resume.toLowerCase().contains('intern'),
      'has_certifications': resume.toLowerCase().contains('certificate'),
      'recommendation': score >= 70 ? 'Good potential fit. Tailor your resume and apply if eligible.' : score >= 50 ? 'Review gaps and strengthen a project before applying.' : 'Build a small project demonstrating required skills first.',
      'platforms': ['Official company careers page', 'Verified university placement portal'],
    };
  }

  if (toolId == 'improve') {
    var lines = resume.split(RegExp(r'[\r\n]+')).map((line) => line.trim()).where((line) => line.isNotEmpty).toList();
    if (lines.length == 1) {
      lines = lines.first.split(RegExp(r'(?<=[.!?])\s+')).where((line) => line.trim().isNotEmpty).toList();
    }
    const headings = <String>{'resume', 'education', 'skills', 'technical skills', 'projects', 'experience', 'work experience', 'certifications', 'summary', 'objective', 'contact', 'languages'};
    lines = lines.where((line) => !headings.contains(line.toLowerCase().replaceAll(':', '')) && line.length >= 12).take(8).toList();
    final improved = lines.map((line) {
      final lower = line.toLowerCase();
      var output = line[0].toUpperCase() + line.substring(1);
      const replacements = <String, String>{
        'worked on ': 'Contributed to ',
        'helped ': 'Supported ',
        'responsible for ': 'Handled ',
        'did ': 'Completed ',
        'made ': 'Created ',
        'used ': 'Applied ',
      };
      for (final entry in replacements.entries) {
        if (lower.startsWith(entry.key)) {
          output = entry.value + line.substring(entry.key.length);
          break;
        }
      }
      if (!output.endsWith('.')) output += '.';
      return <String, dynamic>{
        'original': line,
        'improved': output,
        'improvement_reason': 'Uses clearer action language while preserving meaning and avoiding invented metrics.',
      };
    }).toList();
    return {
      'improved_bullets': improved,
      'general_tips': ['Start each bullet with a precise action verb.', 'Name tools you actually used and explain what you delivered.', 'Add numbers only when you can verify them.', 'Do not claim skills you cannot demonstrate.'],
      'professional_english_phrases': {'instead_of': 'Worked on a project', 'use': 'Describe the specific work you personally completed'},
    };
  }

  throw Exception('This tool needs a supported local generator.');
}
