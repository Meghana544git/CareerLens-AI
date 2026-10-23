import 'dart:convert';
import 'package:dio/dio.dart';
import 'api/session_config.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

const purple=Color(0xFF6557E8), ink=Color(0xFF252640), muted=Color(0xFF777B91), bg=Color(0xFFF6F7FB);
void main()=>runApp(const CareerLensApp());
class CareerLensApp extends StatelessWidget {
 const CareerLensApp({super.key});
 @override Widget build(BuildContext context)=>MaterialApp(title:'CareerLens AI',debugShowCheckedModeBanner:false,theme:ThemeData(useMaterial3:true,colorScheme:ColorScheme.fromSeed(seedColor:purple),scaffoldBackgroundColor:bg,textTheme:GoogleFonts.interTextTheme(),inputDecorationTheme:InputDecorationTheme(filled:true,fillColor:Colors.white,border:OutlineInputBorder(borderRadius:BorderRadius.circular(13),borderSide:const BorderSide(color:Color(0xFFE4E5EF))),enabledBorder:OutlineInputBorder(borderRadius:BorderRadius.circular(13),borderSide:const BorderSide(color:Color(0xFFE4E5EF))),contentPadding:const EdgeInsets.all(15)),filledButtonTheme:FilledButtonThemeData(style:FilledButton.styleFrom(backgroundColor:purple,foregroundColor:Colors.white,padding:const EdgeInsets.symmetric(vertical:14,horizontal:18),shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(12)))),cardTheme:CardThemeData(color:Colors.white,elevation:0,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(18),side:const BorderSide(color:Color(0xFFE8E9F1))))),home:const Shell());
}
class Tool {
 const Tool(this.id,this.title,this.subtitle,this.endpoint,this.icon,this.fields);
 final String id,title,subtitle,endpoint; final IconData icon; final List<Field> fields;
}
class Field {
 const Field(this.key,this.label,this.hint,{this.multi=false,this.required=true});
 final String key,label,hint; final bool multi,required;
}
const jd=Field('job_description','Job description','Paste the full job description…',multi:true);
const resume=Field('resume_text','Resume text (optional)','Paste text or upload your resume first…',multi:true,required:false);
const tools=<Tool>[
 Tool('ats','ATS Resume Score','Match your resume to a role','/api/ats/analyze',Icons.radar_rounded,[jd,Field('job_title','Job title','e.g. Software Engineer',required:false),Field('company_name','Company','e.g. Google',required:false),Field('user_name','Your name','Applicant name',required:false),resume]),
 Tool('cover','Cover Letter','Create a tailored application letter','/api/cover-letter/generate',Icons.description_outlined,[jd,Field('user_name','Your name','Your full name',required:false),resume]),
 Tool('interview','Interview Prep','Predict role-specific interview questions','/api/interview/questions',Icons.forum_outlined,[jd,resume]),
 Tool('skills','Skill Gap Analysis','Find missing skills and learning links','/api/skills/gap',Icons.track_changes_rounded,[jd,resume]),
 Tool('roadmap','Career Roadmap','Plan learning steps for your target role','/api/roadmap/generate',Icons.route_rounded,[Field('target_role','Target role','e.g. Machine Learning Engineer'),resume]),
 Tool('internship','Internship Fit','Evaluate fit for an internship','/api/internship/fit',Icons.school_outlined,[Field('internship_description','Internship description','Paste the full internship description…',multi:true),resume]),
 Tool('improve','Resume Bullet Rewriter','Make bullet points stronger and specific','/api/resume/improve',Icons.auto_awesome_outlined,[Field('resume_text','Resume text','Paste resume text or bullet points…',multi:true),Field('job_description','Target job description (optional)','Paste target JD…',multi:true,required:false)]),
];
class Shell extends StatefulWidget { const Shell({super.key}); @override State<Shell> createState()=>_ShellState(); }
class _ShellState extends State<Shell> {
 final base=TextEditingController(text:'https://career-lens-ai-gilt.vercel.app');
 final chat=TextEditingController();
 final forms=<String,Map<String,TextEditingController>>{};
 final outputs=<String,dynamic>{};
 final messages=<Map<String,String>>[];
 Dio? dio; String? resumeName,resumeText,error; bool busy=false; int page=0; List<dynamic> savedJobs=[]; dynamic dashboardStats; bool historyLoaded=false;
 final nav=<String>['Overview','My Resume','ATS Score','Cover Letter','Interview Prep','Skill Gaps','Career Roadmap','Internship Fit','Improve Resume','Compare Jobs','Career Coach','Saved Jobs','Settings'];
 final icons=<IconData>[Icons.grid_view_rounded,Icons.article_outlined,Icons.radar_rounded,Icons.description_outlined,Icons.forum_outlined,Icons.track_changes_rounded,Icons.route_rounded,Icons.school_outlined,Icons.auto_awesome_outlined,Icons.compare_arrows_rounded,Icons.chat_bubble_outline,Icons.bookmark_border_rounded,Icons.settings_outlined];
 @override void initState(){super.initState(); init();}
 Future<void> init() async {final p=await SharedPreferences.getInstance();base.text=p.getString('career_api')??base.text; connect(base.text,save:false);}
 @override void dispose(){base.dispose();chat.dispose();for(final m in forms.values){for(final c in m.values){c.dispose();}}super.dispose();}
 void connect(String url,{bool save=true}){url=url.trim().replaceAll(RegExp(r'/+$'),'');if(url.isEmpty){setState(()=>error='Enter your backend URL.');return;}dio=Dio(BaseOptions(baseUrl:url,connectTimeout:const Duration(seconds:20),receiveTimeout:const Duration(seconds:90),sendTimeout:const Duration(seconds:90),headers:{'Accept':'application/json'}));configureSession(dio!);if(save)SharedPreferences.getInstance().then((p)=>p.setString('career_api',url));setState(()=>error=null);_loadStats();}
 Future<dynamic> call(String path,{Map<String,dynamic>? data}) async {final r=data==null?await dio!.get(path):await dio!.post(path,data:data,options:Options(contentType:Headers.jsonContentType));final b=r.data;if(b is Map&&b['success']==false)throw Exception(b['error']??'Request failed');return b is Map&&b.containsKey('data')?b['data']:b;}
 Future<dynamic> deleteApi(String path) async {final r=await dio!.delete(path);final b=r.data;if(b is Map&&b['success']==false)throw Exception(b['error']??'Request failed');return b is Map&&b.containsKey('data')?b['data']:b;}
 Future<void> copyText(String value) async {await Clipboard.setData(ClipboardData(text:value));toast('Copied to clipboard.');}
 Future<void> saveCurrentJob(Tool t,dynamic result) async {final c=ctrls(t.id,t.fields);final jdText=c['job_description']?.text.trim()??'';if(jdText.isEmpty){toast('Enter a job description first.');return;}try{await call('/api/jobs/save',data:{'job_title':c['job_title']?.text.trim().isNotEmpty==true?c['job_title']!.text.trim():'Unknown Role','company_name':c['company_name']?.text.trim()??'','job_description':jdText,'ats_score':result is Map?result['ats_score']:null});await loadJobs();toast('Job saved.');}catch(e){showError(e);}}
 Future<void> removeSavedJob(dynamic job) async {if(job is! Map||job['id']==null){toast('This item has no saved-job ID.');return;}try{await deleteApi('/api/jobs/${job['id']}');setState(()=>savedJobs.removeWhere((x)=>x is Map&&x['id']==job['id']));toast('Job removed.');}catch(e){showError(e);}}
 Map<String,TextEditingController> ctrls(String id,List<Field> fields)=>forms.putIfAbsent(id,()=>{for(final f in fields) f.key:TextEditingController(text:f.key=='resume_text'?(resumeText??''):'')});
 String pretty(dynamic v)=>const JsonEncoder.withIndent('  ').convert(v);
 void toast(String s)=>ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(s),behavior:SnackBarBehavior.floating));
 Future<void> runTool(Tool t) async {
  if(dio==null)return; final c=ctrls(t.id,t.fields); final d=<String,dynamic>{};
  for(final f in t.fields){var v=c[f.key]!.text.trim();if(f.key=='resume_text'&&v.isEmpty)v=resumeText??'';if(f.required&&v.isEmpty){toast('Please fill '+f.label);return;}if(v.isNotEmpty)d[f.key]=v;}
  if(t.id=='ats'&&(d['user_name']==null||d['user_name']==''))
    d['user_name']='Applicant';
  setState(()=>busy=true);try{final out=await call(t.endpoint,data:d);setState(()=>outputs[t.id]=out);}catch(e){showError(e);}finally{if(mounted)setState(()=>busy=false);}
 }
 void showError(Object e){final m=e is DioException?((e.response?.data is Map?(e.response!.data as Map)['error']:null)?.toString()??e.message??'Connection failed'):e.toString().replaceFirst('Exception: ','');setState(()=>error=m);toast(m);}
 Future<void> upload() async {
  setState(()=>busy=true);try{final picked=await FilePicker.platform.pickFiles(type:FileType.custom,allowedExtensions:['pdf','docx','txt'],withData:true);if(picked==null)return;final f=picked.files.single;if(f.bytes==null)throw Exception('Could not read this file. Choose it again.');final form=FormData.fromMap({'file':MultipartFile.fromBytes(f.bytes!,filename:f.name)});final r=await dio!.post('/api/resume/upload',data:form);final b=r.data;final out=b is Map&&b.containsKey('data')?b['data']:b;if(b is Map&&b['success']==false)throw Exception(b['error']);setState(() { resumeName = f.name; resumeText = (out is Map ? out['preview'] : '')?.toString(); outputs['upload'] = out; });toast('Resume uploaded successfully.');}catch(e){showError(e);}finally{if(mounted)setState(()=>busy=false);}
 }
 Future<void> sendChat() async {final text=chat.text.trim();if(text.isEmpty)return;setState(() { messages.add({'role':'user','text':text}); chat.clear(); busy = true; });try{final out=await call('/api/chat',data:{'message':text,'resume_text':resumeText??''});String reply=out is Map?(out['response']??out['answer']??out['message']??out['text']??out['content']??pretty(out)).toString():out.toString();setState(()=>messages.add({'role':'assistant','text':reply}));}catch(e){showError(e);}finally{if(mounted)setState(()=>busy=false);}}
 Future<void> loadJobs() async {try{final x=await call('/api/jobs/saved');setState(()=>savedJobs=x is List?x:[]);}catch(e){showError(e);}}
 Future<void> _loadStats() async {try{final x=await call('/api/session/stats');if(mounted)setState(()=>dashboardStats=x);}catch(_){}}
 Future<void> _loadChatHistory() async {if(historyLoaded||dio==null)return;try{final x=await call('/api/chat/history');if(x is List&&mounted){setState(()=>messages.addAll(x.whereType<Map>().map((m)=>{'role':(m['role']??'assistant').toString(),'text':(m['content']??'').toString()})));}}catch(_){}finally{historyLoaded=true;}}
 Future<void> _clearChatHistory() async {try{await call('/api/chat/clear',data:{});if(mounted)setState(()=>messages.clear());toast('Chat history cleared.');}catch(e){showError(e);}}
 Future<void> compare() async {final c=ctrls('compare',[const Field('resume_text','Resume text','',multi:true),const Field('jobs','Jobs','',multi:true)]);final rt=c['resume_text']!.text.trim().isEmpty?(resumeText??''):c['resume_text']!.text.trim();final lines=c['jobs']!.text.split('\n').map((x)=>x.trim()).where((x)=>x.isNotEmpty).toList();if(rt.isEmpty||lines.isEmpty){toast('Add resume text and at least one job.');return;}if(lines.length>5){toast('Maximum 5 jobs.');return;}final jobs=lines.map((x){final p=x.split('|');return {'job_title':p[0].trim(),'company_name':p.length>1?p[1].trim():'','job_description':p.length>2?p.sublist(2).join('|').trim():x};}).toList();setState(()=>busy=true);try{outputs['compare']=await call('/api/jobs/compare',data:{'resume_text':rt,'jobs':jobs});setState((){});}catch(e){showError(e);}finally{if(mounted)setState(()=>busy=false);}}
 @override Widget build(BuildContext context){final wide=MediaQuery.sizeOf(context).width>=900;return Scaffold(body:Row(children:[if(wide)_sidebar(),Expanded(child:Column(children:[_topbar(wide),Expanded(child:dio==null?_settings(first:true):_content())]))]),bottomNavigationBar:wide?null:NavigationBar(selectedIndex:page<4?page:0,onDestinationSelected:(i)=>go([0,1,2,12][i]),destinations:const [NavigationDestination(icon:Icon(Icons.grid_view),label:'Home'),NavigationDestination(icon:Icon(Icons.article_outlined),label:'Resume'),NavigationDestination(icon:Icon(Icons.radar),label:'ATS'),NavigationDestination(icon:Icon(Icons.settings),label:'Settings')]));}
 void go(int i){setState(() { page = i; error = null; });if(i==11)loadJobs();if(i==10)_loadChatHistory();}
 Widget _sidebar()=>Container(width:240,color:Colors.white,child:Column(children:[Padding(padding:const EdgeInsets.fromLTRB(22,25,15,25),child:Row(children:[Container(width:40,height:40,decoration:BoxDecoration(color:purple,borderRadius:BorderRadius.circular(13)),child:const Icon(Icons.bolt,color:Colors.white)),const SizedBox(width:10),Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('CareerLens AI',style:TextStyle(fontWeight:FontWeight.w800,fontSize:16)),Text('AI CAREER STUDIO',style:TextStyle(fontSize:8,color:muted,letterSpacing:1.6))])])),const Align(alignment:Alignment.centerLeft,child:Padding(padding:EdgeInsets.fromLTRB(21,0,0,8),child:Text('WORKSPACE',style:TextStyle(fontSize:10,color:muted,letterSpacing:1.5,fontWeight:FontWeight.w700)))),Expanded(child:ListView.builder(itemCount:nav.length,itemBuilder:(c,i)=>Padding(padding:const EdgeInsets.symmetric(horizontal:11,vertical:2),child:ListTile(dense:true,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(12)),selected:page==i,selectedTileColor:const Color(0xFFEFEDFF),leading:Icon(icons[i],size:19,color:page==i?purple:muted),title:Text(nav[i],style:TextStyle(fontSize:12,fontWeight:page==i?FontWeight.w700:FontWeight.w500,color:page==i?purple:ink)),onTap:()=>go(i))))),Padding(padding:const EdgeInsets.all(14),child:Container(width:double.infinity,padding:const EdgeInsets.all(13),decoration:BoxDecoration(color:const Color(0xFFF4F2FF),borderRadius:BorderRadius.circular(14)),child:const Text('Build your next career move.',style:TextStyle(fontSize:11,fontWeight:FontWeight.w700))))]));
 Widget _topbar(bool wide)=>Container(height:72,padding:EdgeInsets.symmetric(horizontal:wide?30:12),decoration:const BoxDecoration(border:Border(bottom:BorderSide(color:Color(0xFFE9EAF2)))),child:Row(children:[if(!wide)PopupMenuButton<int>(icon:const Icon(Icons.menu),onSelected:go,itemBuilder:(c)=>[for(int i=0;i<nav.length;i++)PopupMenuItem(value:i,child:Text(nav[i]))]),Expanded(child:Column(mainAxisAlignment:MainAxisAlignment.center,crossAxisAlignment:CrossAxisAlignment.start,children:[Text(nav[page],style:const TextStyle(fontWeight:FontWeight.w800,fontSize:17)),const Text('Your personal AI career workspace',style:TextStyle(color:muted,fontSize:11))])),IconButton(onPressed:()=>go(12),icon:const Icon(Icons.settings_outlined)),Container(width:36,height:36,decoration:BoxDecoration(color:const Color(0xFFE4E0FF),borderRadius:BorderRadius.circular(12)),child:const Center(child:Text('CL',style:TextStyle(color:purple,fontWeight:FontWeight.w800))))]));
 Widget _content(){if(page==0)return _dashboard();if(page==1)return _resumePage();if(page>=2&&page<=8)return _toolPage(tools[page-2]);if(page==9)return _comparePage();if(page==10)return _chatPage();if(page==11)return _jobsPage();return _settings();}
 Widget _wrap(Widget child)=>SingleChildScrollView(padding:const EdgeInsets.all(24),child:Center(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:1160),child:child)));
 Widget _dashboard() => _wrap(
    Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(26),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF28234D), Color(0xFF6557E8), Color(0xFF8F83F3)],
            ),
            borderRadius: BorderRadius.circular(23),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 10),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .15),
                  borderRadius: BorderRadius.circular(30),
                ),
                child: const Text(
                  'YOUR AI CAREER PARTNER',
                  style: TextStyle(color: Colors.white, fontSize: 9, letterSpacing: 1.6),
                ),
              ),
              const SizedBox(height: 18),
              Text(
                'Your next opportunity\nstarts with a stronger you.',
                style: GoogleFonts.inter(
                  fontWeight: FontWeight.w800,
                  fontSize: 28,
                  height: 1.2,
                  color: Colors.white,
                  letterSpacing: -.8,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Analyze. Improve. Practice. Get ready to stand out.',
                style: TextStyle(color: Color(0xFFE9E6FF), fontSize: 12),
              ),
              const SizedBox(height: 22),
              Wrap(
                spacing: 10,
                runSpacing: 8,
                children: [
                  FilledButton.icon(
                    onPressed: () => go(1),
                    icon: const Icon(Icons.upload_file),
                    label: const Text('Upload resume'),
                    style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: purple),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => go(2),
                    icon: const Icon(Icons.radar),
                    label: const Text('Run ATS scan'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white54),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        Row(
          children: [
            Expanded(child: _stat('Resume', resumeName ?? 'Not uploaded', Icons.article_outlined)),
            const SizedBox(width: 12),
            Expanded(
              child: _stat(
                'Average ATS score',
                ((dashboardStats is Map ? dashboardStats['avg_ats_score'] : null) ?? '—').toString(),
                Icons.radar_rounded,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _stat(
                'Saved jobs',
                ((dashboardStats is Map ? dashboardStats['saved_jobs'] : null) ?? savedJobs.length).toString(),
                Icons.bookmark_border,
              ),
            ),
          ],
        ),
        const SizedBox(height: 25),
        const Text('Explore your career tools', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
        const SizedBox(height: 5),
        const Text('Choose a tool and strengthen your next application.', style: TextStyle(color: muted, fontSize: 12)),
        const SizedBox(height: 14),
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth > 850 ? 3 : (constraints.maxWidth > 550 ? 2 : 1);
            final extra = [
              ('Compare Jobs', 'Compare up to five roles', Icons.compare_arrows, 9),
              ('AI Career Coach', 'Personal guidance in English or Hindi', Icons.chat_bubble_outline, 10),
            ];
            return GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: columns,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: columns == 1 ? 3.4 : 1.65,
              children: [
                for (final entry in tools.asMap().entries) _toolCard(entry.value, entry.key + 2),
                for (final item in extra) _quickCard(item.$1, item.$2, item.$3, item.$4),
              ],
            );
          },
        ),
        if (error != null) _error(error!),
      ],
    ),
  );
  Widget _stat(String label,String value,IconData icon)=>Card(child:Padding(padding:const EdgeInsets.all(15),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(icon,color:purple,size:22),const SizedBox(height:13),Text(value,style:const TextStyle(fontWeight:FontWeight.w800,fontSize:15),maxLines:1,overflow:TextOverflow.ellipsis),const SizedBox(height:4),Text(label,style:const TextStyle(fontSize:11,color:muted))])));
 Widget _toolCard(Tool t,int index)=>InkWell(onTap:()=>go(index),borderRadius:BorderRadius.circular(18),child:Card(child:Padding(padding:const EdgeInsets.all(17),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Container(width:39,height:39,decoration:BoxDecoration(color:const Color(0xFFF0EEFF),borderRadius:BorderRadius.circular(12)),child:Icon(t.icon,color:purple)),const Spacer(),Text(t.title,style:const TextStyle(fontSize:13,fontWeight:FontWeight.w800)),const SizedBox(height:5),Text(t.subtitle,style:const TextStyle(fontSize:10,color:muted),maxLines:2,overflow:TextOverflow.ellipsis)]))));
 Widget _quickCard(String title,String subtitle,IconData icon,int index)=>InkWell(onTap:()=>go(index),borderRadius:BorderRadius.circular(18),child:Card(child:Padding(padding:const EdgeInsets.all(17),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(icon,color:purple,size:28),const Spacer(),Text(title,style:const TextStyle(fontSize:13,fontWeight:FontWeight.w800)),const SizedBox(height:5),Text(subtitle,style:const TextStyle(fontSize:10,color:muted))]))));
 Widget _resumePage()=>_wrap(Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Your resume',style:TextStyle(fontSize:22,fontWeight:FontWeight.w800)),const SizedBox(height:6),const Text('Upload PDF, DOCX, or TXT to enable career analysis.',style:TextStyle(color:muted,fontSize:12)),const SizedBox(height:18),Card(child:Padding(padding:const EdgeInsets.all(28),child:Column(children:[const Icon(Icons.cloud_upload_outlined,size:50,color:purple),const SizedBox(height:12),Text(resumeName??'Upload your resume',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w800)),const SizedBox(height:7),const Text('PDF, DOCX and TXT supported',style:TextStyle(fontSize:12,color:muted)),const SizedBox(height:18),FilledButton.icon(onPressed:busy?null:upload,icon:const Icon(Icons.file_upload_outlined),label:Text(busy?'Uploading…':'Choose resume')),if(outputs['upload']!=null)...[const SizedBox(height:20),_result(outputs['upload'])]]))),const SizedBox(height:15),const Text('After uploading',style:TextStyle(fontSize:16,fontWeight:FontWeight.w800)),const SizedBox(height:9),for(final e in [('ATS analysis','Match your resume against a job description.',2),('Skill gap analysis','Discover missing requirements.',5),('Resume bullet rewriter','Strengthen your experience bullets.',8)])Card(child:ListTile(leading:const Icon(Icons.check_circle_outline,color:purple),title:Text(e.$1,style:const TextStyle(fontSize:13,fontWeight:FontWeight.w700)),subtitle:Text(e.$2,style:const TextStyle(fontSize:11,color:muted)),trailing:const Icon(Icons.chevron_right),onTap:()=>go(e.$3))),if(error!=null)_error(error!)]));
 Widget _toolPage(Tool t){final c=ctrls(t.id,t.fields);return _wrap(Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Container(width:48,height:48,decoration:BoxDecoration(color:const Color(0xFFEFEDFF),borderRadius:BorderRadius.circular(14)),child:Icon(t.icon,color:purple)),const SizedBox(width:13),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(t.title,style:const TextStyle(fontSize:22,fontWeight:FontWeight.w800)),Text(t.subtitle,style:const TextStyle(fontSize:12,color:muted))]))]),const SizedBox(height:18),Card(child:Padding(padding:const EdgeInsets.all(21),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Add your details',style:TextStyle(fontSize:15,fontWeight:FontWeight.w800)),const SizedBox(height:15),for(final f in t.fields)...[Text(f.label+(f.required?' *':''),style:const TextStyle(fontWeight:FontWeight.w700,fontSize:11)),const SizedBox(height:7),TextField(controller:c[f.key],minLines:f.multi?4:1,maxLines:f.multi?9:1,decoration:InputDecoration(hintText:f.hint,suffixIcon:f.key=='resume_text'&&resumeName!=null?const Icon(Icons.check_circle,color:Colors.green):null)),const SizedBox(height:15)],SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:busy?null:()=>runTool(t),icon:Icon(busy?Icons.hourglass_top:Icons.auto_awesome),label:Text(busy?'Working…':'Generate result')))]))),if(error!=null)_error(error!),if(outputs[t.id]!=null)...[const SizedBox(height:20),Row(children:[const Expanded(child:Text('Your result',style:TextStyle(fontSize:18,fontWeight:FontWeight.w800))),IconButton(tooltip:'Copy result',onPressed:()=>copyText(pretty(outputs[t.id])),icon:const Icon(Icons.copy))]),_result(outputs[t.id]),if(t.id=='ats')Padding(padding:const EdgeInsets.only(top:12),child:OutlinedButton.icon(onPressed:()=>saveCurrentJob(t,outputs[t.id]),icon:const Icon(Icons.bookmark_add_outlined),label:const Text('Save this job')))] ]));}
 Widget _comparePage(){final c=ctrls('compare',[const Field('resume_text','Resume text','',multi:true),const Field('jobs','Jobs','',multi:true)]);return _wrap(Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Compare job opportunities',style:TextStyle(fontSize:22,fontWeight:FontWeight.w800)),const SizedBox(height:7),const Text('Compare up to five job descriptions with your resume.',style:TextStyle(color:muted,fontSize:12)),const SizedBox(height:18),Card(child:Padding(padding:const EdgeInsets.all(20),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Resume text',style:TextStyle(fontSize:11,fontWeight:FontWeight.w700)),const SizedBox(height:7),TextField(controller:c['resume_text'],minLines:4,maxLines:8,decoration:const InputDecoration(hintText:'Paste resume, or upload it on My Resume.')),const SizedBox(height:15),const Text('Jobs (one per line)',style:TextStyle(fontSize:11,fontWeight:FontWeight.w700)),const SizedBox(height:5),const Text('Format: Job title | Company | Full job description',style:TextStyle(fontSize:11,color:muted)),const SizedBox(height:7),TextField(controller:c['jobs'],minLines:5,maxLines:12,decoration:const InputDecoration(hintText:'Software Engineer | Company A | Required skills…\nML Intern | Company B | Python and ML…')),const SizedBox(height:16),FilledButton.icon(onPressed:busy?null:compare,icon:const Icon(Icons.compare_arrows),label:Text(busy?'Comparing…':'Compare jobs'))]))),if(outputs['compare']!=null)_result(outputs['compare']),if(error!=null)_error(error!)]));}
 Widget _chatPage()=>_wrap(Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[const Expanded(child:Text('AI Career Coach',style:TextStyle(fontSize:22,fontWeight:FontWeight.w800))),TextButton.icon(onPressed:_clearChatHistory,icon:const Icon(Icons.delete_outline,size:17),label:const Text('Clear chat'))]),const SizedBox(height:7),const Text('Ask about interviews, applications, learning plans, or career choices. English and Hindi are supported by your backend.',style:TextStyle(color:muted,fontSize:12)),const SizedBox(height:15),Container(height:MediaQuery.sizeOf(context).height*.52,decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(18),border:Border.all(color:const Color(0xFFE7E8F0))),child:messages.isEmpty?const Center(child:Column(mainAxisSize:MainAxisSize.min,children:[Icon(Icons.chat_bubble_outline,color:purple,size:40),SizedBox(height:12),Text('What can I help you with?',style:TextStyle(fontWeight:FontWeight.w800)),SizedBox(height:5),Text('Try: Help me prepare for a Java interview.',style:TextStyle(fontSize:11,color:muted))])):ListView(padding:const EdgeInsets.all(14),children:[for(final m in messages)Align(alignment:m['role']=='user'?Alignment.centerRight:Alignment.centerLeft,child:Container(constraints:const BoxConstraints(maxWidth:650),padding:const EdgeInsets.all(13),margin:const EdgeInsets.only(bottom:10),decoration:BoxDecoration(color:m['role']=='user'?const Color(0xFFEFEDFF):bg,borderRadius:BorderRadius.circular(13)),child:SelectableText(m['text']??'',style:const TextStyle(fontSize:12,height:1.5))))])),const SizedBox(height:10),Row(children:[Expanded(child:TextField(controller:chat,minLines:1,maxLines:4,onSubmitted:(_)=>sendChat(),decoration:const InputDecoration(hintText:'Ask your career coach…'))),const SizedBox(width:8),FilledButton(onPressed:busy?null:sendChat,child:const Icon(Icons.send))]),if(error!=null)_error(error!)]));}
 Widget _jobsPage()=>_wrap(Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
  Row(children:[const Expanded(child:Text('Saved jobs',style:TextStyle(fontSize:22,fontWeight:FontWeight.w800))),OutlinedButton.icon(onPressed:loadJobs,icon:const Icon(Icons.refresh),label:const Text('Refresh'))]),
  const SizedBox(height:8),const Text('Keep track of roles you want to apply for.',style:TextStyle(fontSize:12,color:muted)),const SizedBox(height:15),
  if(savedJobs.isEmpty)const Card(child:Padding(padding:EdgeInsets.all(26),child:Center(child:Column(children:[Icon(Icons.bookmark_border,size:38,color:muted),SizedBox(height:9),Text('No saved jobs yet',style:TextStyle(fontWeight:FontWeight.w800)),SizedBox(height:5),Text('Run an ATS analysis and save the job to see it here.',textAlign:TextAlign.center,style:TextStyle(fontSize:11,color:muted))]))))
  else for(final j in savedJobs)Card(child:ListTile(
    leading:const Icon(Icons.work_outline,color:purple),
    title:Text((j is Map?j['job_title']:'Saved role')?.toString()??'Saved role'),
    subtitle:Text((j is Map?j['company_name']:'')?.toString()??''),
    trailing:IconButton(tooltip:'Remove saved job',icon:const Icon(Icons.delete_outline,color:Color(0xFFB42318)),onPressed:()=>removeSavedJob(j)),
  )),
  if(error!=null)_error(error!)
 ]));
 Widget _settings({bool first = false}) => _wrap(
    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(first ? 'Connect CareerLens AI' : 'Settings', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
      const SizedBox(height: 7),
      const Text('Enter the real URL of your running Flask API backend.', style: TextStyle(fontSize: 12, color: muted)),
      const SizedBox(height: 18),
      Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Backend connection', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
        const SizedBox(height: 8),
        const Text('This must be the URL that serves /api/* routes, not a GitHub repository or static frontend URL.', style: TextStyle(fontSize: 11, color: muted, height: 1.5)),
        const SizedBox(height: 17),
        const Text('API base URL', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 11)),
        const SizedBox(height: 7),
        TextField(controller: base, keyboardType: TextInputType.url, decoration: const InputDecoration(hintText: 'https://your-backend.example.com')),
        const SizedBox(height: 13),
        Wrap(spacing: 8, runSpacing: 8, children: [
          FilledButton.icon(onPressed: () => connect(base.text), icon: const Icon(Icons.link), label: const Text('Connect and save')),
          OutlinedButton(onPressed: () => setState(() => base.text = 'http://127.0.0.1:5000'), child: const Text('Desktop local')),
          OutlinedButton(onPressed: () => setState(() => base.text = 'http://10.0.2.2:5000'), child: const Text('Android emulator')),
        ]),
      ]))),
      const SizedBox(height: 15),
      Card(child: Padding(padding: const EdgeInsets.all(18), child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Connection notes', style: TextStyle(fontWeight: FontWeight.w800)),
        SizedBox(height: 9),
        Text('Desktop local: http://127.0.0.1:5000', style: TextStyle(fontSize: 11, color: muted)),
        Text('Android emulator: http://10.0.2.2:5000', style: TextStyle(fontSize: 11, color: muted)),
        Text('Physical phone: use the computer LAN IP and same Wi-Fi.', style: TextStyle(fontSize: 11, color: muted)),
        Text('Hosted app: enter the deployed Flask backend HTTPS URL. Browser builds need backend CORS configured for their origin.', style: TextStyle(fontSize: 11, color: muted)),
      ]))),
      if (error != null) _error(error!),
    ]),
  );
  Widget _result(dynamic data)=>Container(width:double.infinity,margin:const EdgeInsets.only(top:12),padding:const EdgeInsets.all(16),decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(16),border:Border.all(color:const Color(0xFFE4E5EF))),child:SelectableText(pretty(data),style:const TextStyle(fontFamily:'monospace',fontSize:11,height:1.5,color:ink)));
 Widget _error(String s)=>Container(width:double.infinity,margin:const EdgeInsets.only(top:12),padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:const Color(0xFFFFF1F0),borderRadius:BorderRadius.circular(12),border:Border.all(color:const Color(0xFFF1C5C1))),child:Text(s,style:const TextStyle(color:Color(0xFF9D2922),fontSize:12)));
}