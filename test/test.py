import panel as pn

pn.extension(template="material")

multi_choice = pn.widgets.MultiChoice(
    name="MultiSelect", value=["Apple", "Pear"], options=["Apple", "Banana", "Pear", "Strawberry"]
)

select = pn.widgets.Select(name="Select", options=["Biology", "Chemistry", "Physics"])

pn.Column(multi_choice, select).servable(area="sidebar")
