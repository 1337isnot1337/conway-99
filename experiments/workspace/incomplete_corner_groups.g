# Ordinary generators for the 45 transitive permutation groups on ten points.
Assert(0, NrTransitiveGroups(10) = 45);
output := OutputTextFile("corner-groups.txt", false);;
SetPrintFormattingStatus(output, false);
for number in [1..45] do
    group := TransitiveGroup(10, number);
    generators := GeneratorsOfGroup(group);
    images := List(generators, g -> List([1..10], i -> i^g - 1));
    data := Concatenation([number, Size(group), Length(generators)], Concatenation(images));
    PrintTo(output, JoinStringsWithSeparator(List(data, String), " "), "\n");
od;
CloseStream(output);
QUIT;
