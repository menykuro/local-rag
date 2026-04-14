import {Fragment,useCallback,useContext,useEffect,useRef} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Code as RadixThemesCode,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Link as RadixThemesLink,Separator as RadixThemesSeparator,Text as RadixThemesText,TextField as RadixThemesTextField} from "@radix-ui/themes"
import {Bot as LucideBot,Send as LucideSend,Upload as LucideUpload} from "lucide-react"
import {} from "react-dropzone"
import {ReflexEvent,isNotNullOrUndefined,isTrue,refs} from "$/utils/state"
import {ColorModeContext,EventLoopContext,StateContexts} from "$/utils/context"
import {useDropzone} from "react-dropzone"
import ReactMarkdown from "react-markdown"
import remarkMath from "remark-math"
import remarkGfm from "remark-gfm"
import rehypeKatex from "rehype-katex"
import "katex/dist/katex.min.css"
import rehypeRaw from "rehype-raw"
import rehypeUnwrapImages from "rehype-unwrap-images"
import {Link as ReactRouterLink} from "react-router"
import {PrismAsyncLight as SyntaxHighlighter} from "react-syntax-highlighter"
import oneLight from "react-syntax-highlighter/dist/esm/styles/prism/one-light"
import oneDark from "react-syntax-highlighter/dist/esm/styles/prism/one-dark"
import DebounceInput from "react-debounce-input"
import {jsx} from "@emotion/react"




function Comp_a3022405eb31a429034cbb33f2f34e18 () {
  const ref_upload_dropzone = useRef(null); refs["ref_upload_dropzone"] = ref_upload_dropzone;
const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_drop_ae646d91ee1439fcc88326f40ece9bb0 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.ui___ui____state.handle_upload", ({ ["files"] : _ev_0, ["upload_id"] : "upload_dropzone", ["extra_headers"] : ({  }) }), ({  }), "uploadFiles"))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const on_drop_rejected_2fcedbdc0771e7617b4270e2d1ac8cc9 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("_call_function", ({ ["function"] : (() => (refs['__toast']?.["error"]("", ({ ["title"] : "Files not Accepted", ["description"] : _ev_0.map(((osizayzf) => (osizayzf?.["file"]?.["path"]+": "+osizayzf?.["errors"].map(((wnkiegyk) => wnkiegyk?.["message"])).join(", ")))).join("\n\n"), ["closeButton"] : true, ["style"] : ({ ["whiteSpace"] : "pre-line" }) })))), ["callback"] : null }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const { getRootProps: xdvxrcsn, getInputProps: udaxihhe, isDragActive: bacghqta} = useDropzone(({ ["multiple"] : true, ["accept"] : ({ ["text/plain"] : [".txt"], ["text/markdown"] : [".md", ".markdown"], ["application/pdf"] : [".pdf"], ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"] : [".docx"] }), ["maxFiles"] : 10, ["onDrop"] : on_drop_ae646d91ee1439fcc88326f40ece9bb0, ["id"] : "upload_dropzone", ["onDropRejected"] : on_drop_rejected_2fcedbdc0771e7617b4270e2d1ac8cc9 }));



  return (
    jsx(Fragment,{},jsx(RadixThemesBox,{className:"rx-Upload",css:({ ["border"] : "2px dashed var(--gray-7)", ["borderRadius"] : "xl", ["padding"] : "4", ["height"] : "150px", ["width"] : "100%", ["background"] : "var(--gray-3)", ["textAlign"] : "center" }),id:"upload_dropzone",ref:ref_upload_dropzone,...xdvxrcsn()},jsx("input",{type:"file",...udaxihhe()},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["height"] : "100%" }),direction:"column",justify:"center",gap:"3"},jsx(LucideUpload,{css:({ ["color"] : "var(--blue-11)" }),size:24},),jsx(RadixThemesText,{as:"p",size:"2",weight:"bold"},"Arrastra tus archivos aqu\u00ed"),jsx(RadixThemesText,{as:"p",size:"1"},"o pulsa para navegar"))))
  )
}


function Text_06363cf04cf0708ff0bc99a07f2904a4 () {
  const reflex___state____state__ui___ui____state = useContext(StateContexts.reflex___state____state__ui___ui____state)



  return (
    jsx(RadixThemesText,{as:"p",css:({ ["color"] : "var(--green-11)" }),size:"2",weight:"medium"},reflex___state____state__ui___ui____state.stats_rx_state_)
  )
}


function Fragment_83cefd9fa36fd1d97a2b2360a1132d63 () {
  const reflex___state____state__ui___ui____state = useContext(StateContexts.reflex___state____state__ui___ui____state)



  return (
    jsx(Fragment,{},(!((reflex___state____state__ui___ui____state.stats_rx_state_?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["background"] : "var(--green-3)", ["padding"] : "3", ["borderRadius"] : "md", ["marginTop"] : "3", ["width"] : "100%" })},jsx(Text_06363cf04cf0708ff0bc99a07f2904a4,{},)))):(jsx(Fragment,{},jsx(RadixThemesBox,{},)))))
  )
}


        function ComponentMap_d59534cfa3df3086665270d8af3d1699 () {
            const { resolvedColorMode } = useContext(ColorModeContext)



            return (
                ({ ["h1"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h1",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"6",...props},children))), ["h2"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h2",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"5",...props},children))), ["h3"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h3",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"4",...props},children))), ["h4"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h4",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"3",...props},children))), ["h5"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h5",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"2",...props},children))), ["h6"] : (({node, children, ...props}) => (jsx(RadixThemesHeading,{as:"h6",css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),size:"1",...props},children))), ["p"] : (({node, children, ...props}) => (jsx(RadixThemesText,{as:"p",css:({ ["marginTop"] : "1em", ["marginBottom"] : "1em" }),...props},children))), ["ul"] : (({node, children, ...props}) => (jsx("ul",{css:({ ["listStyleType"] : "disc", ["marginTop"] : "1em", ["marginBottom"] : "1em", ["marginLeft"] : "1.5rem", ["direction"] : "column" }),...props},children))), ["ol"] : (({node, children, ...props}) => (jsx("ol",{css:({ ["listStyleType"] : "decimal", ["marginTop"] : "1em", ["marginBottom"] : "1em", ["marginLeft"] : "1.5rem", ["direction"] : "column" }),...props},children))), ["li"] : (({node, children, ...props}) => (jsx("li",{css:({ ["marginTop"] : "0.5em", ["marginBottom"] : "0.5em" }),...props},children))), ["a"] : (({node, children, ...props}) => (jsx(RadixThemesLink,{css:({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) }),href:"#",...props},children))), ["code"] : (({node, children, ...props}) => (jsx(RadixThemesCode,{...props},children))), ["pre"] : (({node, ...rest}) => { const {node: childNode, className, children: components, ...props} = rest.children.props; const children = String(Array.isArray(components) ? components.join('\n') : components).replace(/\n$/, ''); const match = (className || '').match(/language-(?<lang>.*)/); let _language = match ? match[1] : ''; ;             return jsx(SyntaxHighlighter,{children:children,css:({ ["marginTop"] : "1em", ["marginBottom"] : "1em" }),language:_language,style:((resolvedColorMode?.valueOf?.() === "light"?.valueOf?.()) ? oneLight : oneDark),wrapLongLines:true,...props},);         }) })
            )
        }
        

function Box_95d6983ed0ddd1372378a8c17a06f661 () {
  const reflex___state____state__ui___ui____state = useContext(StateContexts.reflex___state____state__ui___ui____state)



  return (
    jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["flex"] : "1", ["overflowY"] : "auto", ["padding"] : "6" })},Array.prototype.map.call(reflex___state____state__ui___ui____state.chat_history_rx_state_ ?? [],((message_rx_state_,index_3ffd862380bb1e1f9961a4c967344238)=>(jsx(RadixThemesFlex,{css:({ ["width"] : "100%", ["marginBottom"] : "3" }),justify:((message_rx_state_?.["role"]?.valueOf?.() === "user"?.valueOf?.()) ? "end" : "start"),key:index_3ffd862380bb1e1f9961a4c967344238},jsx(RadixThemesBox,{css:({ ["background"] : ((message_rx_state_?.["role"]?.valueOf?.() === "user"?.valueOf?.()) ? "var(--blue-5)" : "var(--gray-3)"), ["color"] : ((message_rx_state_?.["role"]?.valueOf?.() === "user"?.valueOf?.()) ? "white" : "inherit"), ["borderRadius"] : "xl", ["padding"] : "4", ["maxWidth"] : "85%", ["boxShadow"] : "0 10px 15px -3px rgb(0 0 0 / 0.1)" })},jsx("div",{},jsx(ReactMarkdown,{components:ComponentMap_d59534cfa3df3086665270d8af3d1699(),rehypePlugins:[rehypeKatex, rehypeRaw, rehypeUnwrapImages],remarkPlugins:[remarkMath, remarkGfm]},message_rx_state_?.["content"]))))))))
  )
}


function Debounceinput_39c96a48c1fabf40e9288a509c47bf4a () {
  const reflex___state____state__ui___ui____state = useContext(StateContexts.reflex___state____state__ui___ui____state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_change_96c1a6c201651979989d6a82f29c072a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.ui___ui____state.set_current_question", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const on_key_down_befde3f6a551d97bfdb8ad9ebf3ddee9 = useCallback(((_e) => (addEvents([((reflex___state____state__ui___ui____state.current_question_rx_state_.split("").length > 0) ? (ReflexEvent("_call_script", ({ ["javascript_code"] : "if(event.key === 'Enter' && !event.shiftKey) { document.getElementById('super_send_btn').click(); }", ["callback"] : null }), ({  }))) : (ReflexEvent("_call_script", ({ ["javascript_code"] : "", ["callback"] : null }), ({  }))))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__ui___ui____state])

  return (
    jsx(DebounceInput,{css:({ ["width"] : "100%" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_96c1a6c201651979989d6a82f29c072a,onKeyDown:on_key_down_befde3f6a551d97bfdb8ad9ebf3ddee9,placeholder:"Haz a JARVIS cualquier pregunta de tu temario local...",radius:"large",size:"3",value:(isNotNullOrUndefined(reflex___state____state__ui___ui____state.current_question_rx_state_) ? reflex___state____state__ui___ui____state.current_question_rx_state_ : "")},)
  )
}


function Button_2f3ba1cd360c8fe9b81dc1513c100565 () {
  const ref_super_send_btn = useRef(null); refs["ref_super_send_btn"] = ref_super_send_btn;
const reflex___state____state__ui___ui____state = useContext(StateContexts.reflex___state____state__ui___ui____state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_856b84a7ca6e0bec038af27f8a83054c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.ui___ui____state.answer_query", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{css:({ ["cursor"] : "pointer" }),id:"super_send_btn",loading:reflex___state____state__ui___ui____state.is_processing_rx_state_,onClick:on_click_856b84a7ca6e0bec038af27f8a83054c,radius:"large",ref:ref_super_send_btn,size:"3"},jsx(LucideSend,{},))
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100vw", ["height"] : "100vh" }),direction:"row",gap:"0"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["@media screen and (min-width: 0)"] : ({ ["width"] : "100%" }), ["@media screen and (min-width: 30em)"] : ({ ["width"] : "100%" }), ["@media screen and (min-width: 48em)"] : ({ ["width"] : "30%" }), ["minWidth"] : "320px", ["maxWidth"] : "400px", ["height"] : "100vh", ["padding"] : "6", ["background"] : "var(--gray-2)", ["borderRight"] : "1px solid var(--gray-4)", ["alignItems"] : "start" }),direction:"column",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(LucideBot,{css:({ ["color"] : "var(--blue-11)" }),size:32},),jsx(RadixThemesHeading,{css:({ ["color"] : "var(--blue-11)" }),size:"6",weight:"bold"},"JARVIS Mini")),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "var(--gray-11)", ["marginBottom"] : "4" }),size:"2"},"RAG Architecture Dashboard"),jsx(RadixThemesSeparator,{size:"4"},),jsx(RadixThemesHeading,{css:({ ["marginTop"] : "4", ["marginBottom"] : "2" }),size:"4"},"Ingesta Documental"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "var(--gray-11)" }),size:"2"},"Alimenta la red neuronal a\u00f1adiendo PDFs o TXTs. Se segmentar\u00e1n autom\u00e1ticamente in FAISS."),jsx(RadixThemesBox,{css:({ ["width"] : "100%", ["marginTop"] : "2" })},jsx(Comp_a3022405eb31a429034cbb33f2f34e18,{},)),jsx(Fragment_83cefd9fa36fd1d97a2b2360a1132d63,{},),jsx(RadixThemesSeparator,{css:({ ["marginTop"] : "6", ["marginBottom"] : "4" }),size:"4"},),jsx(RadixThemesHeading,{size:"4"},"Ajustes del Modelo LLM"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "var(--gray-11)" }),size:"2"},"Modelo Base: Qwen 3.5 0.8B"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "var(--gray-11)" }),size:"2"},"Modo L\u00f3gico: Solo-RAG"),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{align:"center",as:"p",css:({ ["color"] : "var(--gray-9)", ["width"] : "100%" }),size:"1"},"TFG Project")),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%", ["height"] : "100vh", ["position"] : "relative" }),direction:"column",justify:"between",gap:"3"},jsx(Box_95d6983ed0ddd1372378a8c17a06f661,{},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%", ["padding"] : "4", ["background"] : "var(--gray-2)", ["borderTop"] : "1px solid var(--gray-4)" }),direction:"row",gap:"3"},jsx(Debounceinput_39c96a48c1fabf40e9288a509c47bf4a,{},),jsx(Button_2f3ba1cd360c8fe9b81dc1513c100565,{},)))),jsx("title",{},"JARVIS RAG - Chat"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}