#https://discourse.holoviz.org/t/how-to-move-detach-single-pane-from-a-dashboard-into-a-separate-browser-window/4545/4


import panel as pn
import uuid

pn.extension(template="fast")

def get_object_id():
    return pn.state.session_args.get("id", [b""])[0].decode(encoding="utf8")

def serve_no_object_id_app():
    unique_id = str(uuid.uuid4()) 

    js_pane = pn.pane.HTML(visible=False, height=0, width=0, sizing_mode="fixed", margin=0)
    open_button = pn.widgets.Button(name = "Open the component below in another window", button_type="primary")
    
    component = pn.widgets.TextInput(name="Some component")
    
    @pn.depends(open_button, watch=True)
    def open_new_window(_):
        pn.state.cache[unique_id]=component
        js_pane.object=f"""<script>
window.open("?id={unique_id}", '_blank', 'left=500,height=400,width=400')
</script>
"""
        js_pane.object = ""
    

    pn.Column("# Main Page", open_button, component, js_pane).servable()

def serve_object_id_app(object_id):
    component = pn.state.cache.get(object_id, pn.pane.Markdown("Not found"))
    pn.Column(f"# Page {object_id}", component).servable()

object_id = get_object_id()

if not object_id:
    serve_no_object_id_app()
else:
    serve_object_id_app(object_id)